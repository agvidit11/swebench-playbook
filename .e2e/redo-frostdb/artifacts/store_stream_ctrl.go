package frostdb

// POSITIVE CONTROL for the A3 GATE-4 assertion sketch (redo-frostdb, 2026-09-22).
// A hand-written streaming fan-out that satisfies the card's DESIRED path: the block
// is produced once and its bytes reach the sinks while it is still being produced, so
// a stalled sink holds the others back and nothing is ever held whole in memory.
// Throwaway control code; it exists only to prove the sketch is satisfiable.

import (
	"context"
	"errors"
	"fmt"
	"io"
	"path/filepath"
	"sync"
)

type ctrlLeg struct {
	sink DataSink
	pw   *io.PipeWriter
	dead bool
	err  error
}

func (t *TableBlock) persistStreaming() error {
	sinks := t.table.db.sinks
	if len(sinks) == 0 {
		return nil
	}
	fileName := filepath.Join(t.table.db.name, t.table.name, t.ulid.String(), "data.parquet")

	legs := make([]*ctrlLeg, 0, len(sinks))
	var wg sync.WaitGroup
	var mu sync.Mutex

	for _, s := range sinks {
		pr, pw := io.Pipe()
		leg := &ctrlLeg{sink: s, pw: pw}
		legs = append(legs, leg)
		wg.Add(1)
		go func(l *ctrlLeg, r *io.PipeReader) {
			defer wg.Done()
			err := l.sink.Upload(context.Background(), fileName, r)
			if err != nil {
				// Detach this leg: further writes to it must not block the pass.
				_ = r.CloseWithError(err)
				mu.Lock()
				l.dead = true
				l.err = fmt.Errorf("sink %s: %w", l.sink.String(), err)
				mu.Unlock()
				if delErr := l.sink.Delete(context.Background(), fileName); delErr != nil {
					mu.Lock()
					l.err = fmt.Errorf("%w (delete: %v)", l.err, delErr)
					mu.Unlock()
				}
				return
			}
			_ = r.Close()
		}(leg, pr)
	}

	w := &ctrlFanout{legs: legs, mu: &mu}
	serErr := t.Serialize(w)

	for _, l := range legs {
		if serErr != nil {
			_ = l.pw.CloseWithError(serErr)
		} else {
			_ = l.pw.Close()
		}
	}
	wg.Wait()

	var errs []error
	if serErr != nil {
		errs = append(errs, fmt.Errorf("failed to serialize block: %w", serErr))
	}
	for _, l := range legs {
		if l.err != nil {
			errs = append(errs, l.err)
		}
	}
	if len(errs) > 0 {
		return errors.Join(errs...)
	}
	t.table.metrics.blockPersisted.Inc()
	return nil
}

type ctrlFanout struct {
	legs []*ctrlLeg
	mu   *sync.Mutex
}

func (f *ctrlFanout) Write(p []byte) (int, error) {
	live := 0
	for _, l := range f.legs {
		f.mu.Lock()
		dead := l.dead
		f.mu.Unlock()
		if dead {
			continue
		}
		if _, err := l.pw.Write(p); err != nil {
			f.mu.Lock()
			l.dead = true
			f.mu.Unlock()
			continue
		}
		live++
	}
	if live == 0 {
		return len(p), nil
	}
	return len(p), nil
}
