// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package fsm

import "fmt"

type FSM map[string]map[string]struct{}

func NewFSM(transitionsDefinition map[string][]string) FSM {
	fsm := map[string]map[string]struct{}{}

	for current, allowedTargets := range transitionsDefinition {
		fsm[current] = map[string]struct{}{}
		for _, allowedTarget := range allowedTargets {
			fsm[current][allowedTarget] = struct{}{}
		}
	}
	return fsm
}

func (fsm FSM) Transition(from string, to string) error {
	_, ok := fsm[from][to]
	if !ok {
		return fmt.Errorf("invalid transition: %v -> %v", from, to)
	}
	return nil
}
