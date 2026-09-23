package frostdb

// GATE-4 A3-LOCAL assertion SKETCH for candidate C1 (streaming multi-sink persist),
// redo run 2026-09-22. Throwaway probe harness authored by Claude in a scratch clone.
// This is NOT a task tests/ artifact and never becomes one.
//
// The difference from the killed run's sketch is S2: it OBSERVES SERIALIZATION
// COMPLETION. The old sketch only observed that two Uploads could overlap, which a
// fully-buffered implementation satisfies trivially.

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/parquet-go/parquet-go"

	"github.com/polarsignals/frostdb/dynparquet"
	"github.com/polarsignals/frostdb/samples"
)

// gRows is deliberately large: the discriminating assertion must not be decidable
// by an incidental 4 KB / 64 KB buffer somewhere in the pipeline.
const gRows = 60000

type gSink struct {
	name string

	mu      sync.Mutex
	buf     bytes.Buffer
	uploads int
	deletes int

	read int64 // bytes this sink has consumed from its reader

	started   chan struct{}
	onceStart sync.Once

	eof     chan struct{} // closed when this sink has read its copy through to EOF
	onceEOF sync.Once

	// holdBeforeRead, if non-nil, blocks Upload BEFORE a single byte is consumed.
	holdBeforeRead <-chan struct{}

	// failAfter > 0 makes Upload fail after consuming that many bytes.
	failAfter int
}

func newGSink(name string) *gSink {
	return &gSink{name: name, started: make(chan struct{}), eof: make(chan struct{})}
}

func (s *gSink) String() string { return s.name }

type countingReader struct {
	r io.Reader
	s *gSink
}

func (c countingReader) Read(p []byte) (int, error) {
	n, err := c.r.Read(p)
	atomic.AddInt64(&c.s.read, int64(n))
	return n, err
}

func (s *gSink) Upload(_ context.Context, _ string, r io.Reader) error {
	s.onceStart.Do(func() { close(s.started) })
	s.mu.Lock()
	s.uploads++
	s.mu.Unlock()

	if s.holdBeforeRead != nil {
		select {
		case <-s.holdBeforeRead:
		case <-time.After(120 * time.Second):
			return errors.New("g: hold never released")
		}
	}

	cr := countingReader{r: r, s: s}

	if s.failAfter > 0 {
		_, _ = io.Copy(io.Discard, io.LimitReader(cr, int64(s.failAfter)))
		// Drain in the background so a live writer is never wedged by our failure.
		go func() { _, _ = io.Copy(io.Discard, r) }()
		return errors.New("g: injected failure in sink " + s.name)
	}

	var local bytes.Buffer
	_, err := io.Copy(&local, cr)
	s.mu.Lock()
	s.buf = local
	s.mu.Unlock()
	if err == nil {
		s.onceEOF.Do(func() { close(s.eof) })
	}
	return err
}

func (s *gSink) Delete(_ context.Context, _ string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.deletes++
	return nil
}

func (s *gSink) consumed() int64 { return atomic.LoadInt64(&s.read) }

func (s *gSink) bytesLen() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.buf.Len()
}

func (s *gSink) deleteCount() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.deletes
}

func (s *gSink) uploadCount() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.uploads
}

func (s *gSink) rows(t *testing.T) int64 {
	t.Helper()
	s.mu.Lock()
	b := append([]byte(nil), s.buf.Bytes()...)
	s.mu.Unlock()
	if len(b) == 0 {
		return -1
	}
	f, err := parquet.OpenFile(bytes.NewReader(b), int64(len(b)))
	if err != nil {
		t.Logf("g: sink %s bytes (%d) do not parse as parquet: %v", s.name, len(b), err)
		return -1
	}
	return f.NumRows()
}

func gSetup(t *testing.T, sinks ...DataSink) *TableBlock {
	t.Helper()
	opts := []Option{WithManualBlockRotation()}
	for _, s := range sinks {
		opts = append(opts, WithWriteOnlyStorage(s))
	}
	cs, err := New(opts...)
	if err != nil {
		t.Fatalf("New: %v", err)
	}
	t.Cleanup(func() { _ = cs.Close() })
	db, err := cs.DB(context.Background(), "gdb")
	if err != nil {
		t.Fatalf("DB: %v", err)
	}
	tbl, err := db.Table("gtbl", NewTableConfig(dynparquet.SampleDefinition()))
	if err != nil {
		t.Fatalf("Table: %v", err)
	}
	ss := make(samples.Samples, 0, gRows)
	for i := 0; i < gRows; i++ {
		ss = append(ss, samples.Sample{
			ExampleType: "cpu",
			Labels: map[string]string{
				"node": fmt.Sprintf("n%06d", i),
				"pod":  fmt.Sprintf("p%06d", i*7919%gRows),
			},
			Timestamp: int64(i),
			Value:     int64(i) * 2654435761,
		})
	}
	rec, err := ss.ToRecord()
	if err != nil {
		t.Fatalf("ToRecord: %v", err)
	}
	if _, err := tbl.InsertRecord(context.Background(), rec); err != nil {
		t.Fatalf("InsertRecord: %v", err)
	}
	return tbl.ActiveBlock()
}

// ---------------------------------------------------------------------------
// S1 — every configured sink ends up holding the complete block.
// ---------------------------------------------------------------------------
func TestS1AllSinksCompleteBlock(t *testing.T) {
	a, b, c := newGSink("a"), newGSink("b"), newGSink("c")
	blk := gSetup(t, a, b, c)
	if err := blk.Persist(); err != nil {
		t.Fatalf("S1: Persist returned %v", err)
	}
	for _, s := range []*gSink{a, b, c} {
		if got := s.rows(t); got != gRows {
			t.Errorf("S1: sink %s got %d rows (%d bytes), want %d", s.name, got, s.bytesLen(), gRows)
		}
	}
	t.Logf("S1: serialized block size = %d bytes", a.bytesLen())
}

// ---------------------------------------------------------------------------
// S2 — THE DISCRIMINATOR. Observes serialization completion.
//
// Sink a enters Upload and consumes nothing. While a has consumed zero bytes, no
// other sink may observe the end of its copy. A sink can only reach EOF if the
// block was produced to completion without a consuming it -- i.e. the whole block
// was materialised first. This is the assertion the killed run did not have.
// ---------------------------------------------------------------------------
func TestS2NoSinkReachesEndWhileAnotherHasConsumedNothing(t *testing.T) {
	release := make(chan struct{})
	a, b := newGSink("a"), newGSink("b")
	a.holdBeforeRead = release
	blk := gSetup(t, a, b)

	done := make(chan error, 1)
	go func() { done <- blk.Persist() }()

	// Both uploads must at least have begun; that much the old sketch checked too.
	for _, s := range []*gSink{a, b} {
		select {
		case <-s.started:
		case <-time.After(60 * time.Second):
			close(release)
			t.Fatalf("S2: sink %s Upload never began", s.name)
		}
	}

	// The discriminating window: a has consumed nothing. b must not reach the end.
	select {
	case <-b.eof:
		if a.consumed() != 0 {
			t.Fatalf("S2: harness fault -- a consumed %d bytes before the check", a.consumed())
		}
		close(release)
		<-done
		t.Fatalf("S2: sink b reached the end of its copy (%d bytes) while sink a had "+
			"consumed nothing -- the block was produced to completion before the sinks "+
			"consumed it", b.bytesLen())
	case <-time.After(5 * time.Second):
		// Good: nobody can finish while a is stalled.
	}
	if a.consumed() != 0 {
		t.Fatalf("S2: harness fault -- a consumed %d bytes while held", a.consumed())
	}

	close(release)
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("S2: Persist returned %v after release", err)
		}
	case <-time.After(120 * time.Second):
		t.Fatalf("S2: Persist did not return within 120s after release")
	}
	for _, s := range []*gSink{a, b} {
		if got := s.rows(t); got != gRows {
			t.Errorf("S2: after release sink %s got %d rows, want %d", s.name, got, gRows)
		}
	}
}

// ---------------------------------------------------------------------------
// S3 — a sink failing partway is named, cleaned up, and does not cost the others.
// ---------------------------------------------------------------------------
func TestS3MidStreamFailureIsolation(t *testing.T) {
	a, b := newGSink("a"), newGSink("b")
	b.failAfter = 64
	blk := gSetup(t, a, b)

	done := make(chan error, 1)
	go func() { done <- blk.Persist() }()
	var err error
	select {
	case err = <-done:
	case <-time.After(120 * time.Second):
		t.Fatalf("S3: Persist did not return within 120s")
	}
	if err == nil {
		t.Errorf("S3: Persist returned nil, want an error identifying sink b")
	} else if !strings.Contains(err.Error(), "b") {
		t.Errorf("S3: error %q does not identify the failing sink b", err.Error())
	}
	if got := a.rows(t); got != gRows {
		t.Errorf("S3: healthy sink a got %d rows, want %d", got, gRows)
	}
	if b.deleteCount() < 1 {
		t.Errorf("S3: failing sink b had Delete called %d times, want >= 1", b.deleteCount())
	}
}

// ---------------------------------------------------------------------------
// S4 — regression: the zero-sink and single-sink shapes are unchanged.
// ---------------------------------------------------------------------------
func TestS4ZeroAndSingleSinkRegression(t *testing.T) {
	blk := gSetup(t)
	if err := blk.Persist(); err != nil {
		t.Errorf("S4: zero-sink Persist returned %v, want nil", err)
	}

	only := newGSink("only")
	blk2 := gSetup(t, only)
	if err := blk2.Persist(); err != nil {
		t.Fatalf("S4: single-sink Persist returned %v", err)
	}
	if got := only.rows(t); got != gRows {
		t.Errorf("S4: single sink got %d rows, want %d", got, gRows)
	}
	if only.uploadCount() != 1 {
		t.Errorf("S4: single sink Upload called %d times, want 1", only.uploadCount())
	}
}
