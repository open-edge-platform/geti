// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package common

type NextPage struct {
	Skip  int32
	Limit int32
}

func CalculateNextPage(totalRecordsCount, skipRequested, limitRequested int32) NextPage {
	nextPageSkip := skipRequested + limitRequested
	leftRecordsCount := totalRecordsCount - nextPageSkip
	var nextPageLimit int32
	if leftRecordsCount <= 0 {
		nextPageLimit = 0
	} else if leftRecordsCount > limitRequested {
		nextPageLimit = limitRequested
	} else {
		nextPageLimit = leftRecordsCount
	}

	return NextPage{
		Skip:  nextPageSkip,
		Limit: nextPageLimit,
	}
}
