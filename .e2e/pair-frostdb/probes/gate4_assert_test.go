package frostdb

// GATE-4 graded assertion for candidate C1 (streaming multi-sink persist).
// Authored by Claude as a PROBE harness in a throwaway clone. This is NOT a
// task `tests/` artifact and never becomes one.

import (
	"bytes"
	"context"
	"errors"
	"io"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/parquet-go/parquet-go"

	"github.com/polarsignals/frostdb/dynparquet"
	"github.com/polarsignals/frostdb/samples"
)

type g4Sink struct {
	name string

	mu      sync.Mutex
	buf     bytes.Buffer
	uploads int
	deletes int

	started chan struct{} // closed when Upload begins
	once    sync.Once

	// gate, if non-nil, is waited on after Upload starts and before the body
	// is drained. Used to prove two uploads can be in flight at once.
	gate <-chan struct{}

	// failAfter > 0 makes Upload return an error after reading that many bytes.
	failAfter int
}

func newG4Sink(name string) *g4Sink {
	return &g4Sink{name: name, started: make(chan struct{})}
}

func (s *g4Sink) String() string { return s.name }

func (s *g4Sink) Upload(_ context.Context, _ string, r io.Reader) error {
	s.once.Do(func() { close(s.started) })
	s.mu.Lock()
	s.uploads++
	s.mu.Unlock()

	if s.gate != nil {
		select {
		case <-s.gate:
		case <-time.After(10 * time.Second):
			return errors.New("g4: gate never opened; uploads are not concurrent")
		}
	}

	if s.failAfter > 0 {
		lim := io.LimitReader(r, int64(s.failAfter))
		n, _ := io.Copy(io.Discard, lim)
		_ = n
		// Drain the rest so a pipe writer is not blocked forever, then fail.
		go func() { _, _ = io.Copy(io.Discard, r) }()
		return errors.New("g4: injected failure in sink " + s.name)
	}

	s.mu.Lock()
	defer s.mu.Unlock()
	_, err := io.Copy(&s.buf, r)
	return err
}

func (s *g4Sink) Delete(_ context.Context, _ string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.deletes++
	return nil
}

func (s *g4Sink) bytesLen() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.buf.Len()
}

func (s *g4Sink) rows(t *testing.T) int64 {
	t.Helper()
	s.mu.Lock()
	b := append([]byte(nil), s.buf.Bytes()...)
	s.mu.Unlock()
	if len(b) == 0 {
		return -1
	}
	f, err := parquet.OpenFile(bytes.NewReader(b), int64(len(b)))
	if err != nil {
		t.Logf("g4: sink %s bytes do not parse as parquet: %v", s.name, err)
		return -1
	}
	return f.NumRows()
}

const g4Rows = 4

func g4Setup(t *testing.T, sinks ...DataSink) *TableBlock {
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
	db, err := cs.DB(context.Background(), "g4db")
	if err != nil {
		t.Fatalf("DB: %v", err)
	}
	tbl, err := db.Table("g4tbl", NewTableConfig(dynparquet.SampleDefinition()))
	if err != nil {
		t.Fatalf("Table: %v", err)
	}
	s := samples.Samples{
		{ExampleType: "cpu", Labels: map[string]string{"node": "n1"}, Timestamp: 1, Value: 1},
		{ExampleType: "cpu", Labels: map[string]string{"node": "n2"}, Timestamp: 2, Value: 2},
		{ExampleType: "cpu", Labels: map[string]string{"node": "n3"}, Timestamp: 3, Value: 3},
		{ExampleType: "cpu", Labels: map[string]string{"node": "n4"}, Timestamp: 4, Value: 4},
	}
	rec, err := s.ToRecord()
	if err != nil {
		t.Fatalf("ToRecord: %v", err)
	}
	if _, err := tbl.InsertRecord(context.Background(), rec); err != nil {
		t.Fatalf("InsertRecord: %v", err)
	}
	return tbl.ActiveBlock()
}

// A1 — every sink receives a complete, parseable block.
func TestG4A1AllSinksReceiveCompleteBlock(t *testing.T) {
	a, b, c := newG4Sink("a"), newG4Sink("b"), newG4Sink("c")
	blk := g4Setup(t, a, b, c)
	if err := blk.Persist(); err != nil {
		t.Fatalf("A1: Persist returned %v", err)
	}
	for _, s := range []*g4Sink{a, b, c} {
		if got := s.rows(t); got != g4Rows {
			t.Errorf("A1: sink %s got %d rows (%d bytes), want %d", s.name, got, s.bytesLen(), g4Rows)
		}
	}
}

// A2 — two uploads can be in flight at the same time.
// a blocks until b has started. A sequential implementation cannot pass.
func TestG4A2UploadsAreConcurrent(t *testing.T) {
	a, b := newG4Sink("a"), newG4Sink("b")
	a.gate = b.started
	blk := g4Setup(t, a, b)

	done := make(chan error, 1)
	go func() { done <- blk.Persist() }()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("A2: Persist returned %v", err)
		}
	case <-time.After(25 * time.Second):
		t.Fatalf("A2: Persist did not return within 25s -- uploads are serialized")
	}
	if got := a.rows(t); got != g4Rows {
		t.Errorf("A2: sink a got %d rows, want %d", got, g4Rows)
	}
	if got := b.rows(t); got != g4Rows {
		t.Errorf("A2: sink b got %d rows, want %d", got, g4Rows)
	}
}

// A3 — one sink failing must not cost the healthy sink its copy; the error must
// name the failing sink; the failing sink's Delete must be called.
func TestG4A3FailureIsolation(t *testing.T) {
	a, b := newG4Sink("a"), newG4Sink("b")
	b.failAfter = 16
	blk := g4Setup(t, a, b)

	done := make(chan error, 1)
	go func() { done <- blk.Persist() }()
	var err error
	select {
	case err = <-done:
	case <-time.After(25 * time.Second):
		t.Fatalf("A3: Persist did not return within 25s")
	}
	if err == nil {
		t.Errorf("A3: Persist returned nil, want an error naming sink b")
	} else if !strings.Contains(err.Error(), "b") {
		t.Errorf("A3: error %q does not identify the failing sink b", err.Error())
	}
	if got := a.rows(t); got != g4Rows {
		t.Errorf("A3: healthy sink a got %d rows (%d bytes), want %d", got, a.bytesLen(), g4Rows)
	}
	b.mu.Lock()
	dels := b.deletes
	b.mu.Unlock()
	if dels == 0 {
		t.Errorf("A3: failing sink b had Delete called %d times, want >=1", dels)
	}
}

// A4 — regression: zero sinks and one sink keep working.
func TestG4A4ZeroAndSingleSinkRegression(t *testing.T) {
	blk := g4Setup(t)
	if err := blk.Persist(); err != nil {
		t.Errorf("A4: zero-sink Persist returned %v, want nil", err)
	}

	a := newG4Sink("a")
	blk2 := g4Setup(t, a)
	if err := blk2.Persist(); err != nil {
		t.Fatalf("A4: single-sink Persist returned %v", err)
	}
	if got := a.rows(t); got != g4Rows {
		t.Errorf("A4: single sink got %d rows, want %d", got, g4Rows)
	}
}
