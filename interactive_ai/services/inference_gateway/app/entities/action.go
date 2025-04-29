// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

type ActionType string

const (
	Predict      ActionType = "predict"
	BatchPredict ActionType = "batch_predict"
	Explain      ActionType = "explain"
	BatchExplain ActionType = "batch_explain"
)

var SupportedActions = []ActionType{Predict, BatchPredict, Explain, BatchExplain}

// Using a map for constant-time lookup
var supportedActions = map[ActionType]bool{
	Predict:      true,
	BatchPredict: true,
	Explain:      true,
	BatchExplain: true,
}

// IsActionSupported returns true if the action is one of the supported action verbs
func IsActionSupported(action string) bool {
	_, exists := supportedActions[ActionType(action)]
	return exists
}
