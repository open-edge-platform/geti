// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package fsm

var UserStatusFSM = NewFSM(
	map[string][]string{
		"RGS": {"RGS", "ACT", "DEL"},
		"ACT": {"ACT", "RGS", "SSP", "DEL"},
		"SSP": {"SSP", "ACT", "DEL"},
		"DEL": {"DEL"},
		"REQ": {"REQ", "ACT", "DEL"},
	},
)
