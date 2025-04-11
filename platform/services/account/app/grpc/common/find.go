// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package common

import (
	"fmt"

	grpcUtils "account_service/app/grpc/utils"
	"common/utils"

	"golang.org/x/exp/slices"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

func CountAll(tx *gorm.DB, model interface{}) (int32, error) {
	var totalCount int64
	dbResult := tx.Model(&model).Count(&totalCount)
	if dbResult.Error != nil {
		logger.Errorf("error during user count: %v", dbResult.Error)
		return 0, status.Errorf(codes.Unknown, "unexpected error")
	}

	return int32(totalCount), nil
}

func CreateOrderQuery(model any, sortBy string, sortDirection string) (string, error) {
	fieldNames := grpcUtils.GetFieldNames(model)
	possibleSortTargets := make([]string, len(fieldNames))

	for i, pascalCaseField := range fieldNames {
		possibleSortTargets[i] = grpcUtils.ToCamelCase(pascalCaseField)
	}
	possibleSortDirections := []string{"asc", "desc"}

	if !slices.Contains(possibleSortTargets, sortBy) {
		return "", status.Errorf(codes.InvalidArgument,
			"invalid 'SortBy' value, possible targets: %v", possibleSortTargets)
	}
	if !slices.Contains(possibleSortDirections, sortDirection) {
		return "", status.Errorf(codes.InvalidArgument,
			"invalid 'SortDirection' value, possible directions: %v", possibleSortDirections)
	}

	snakeCasedSortBy := grpcUtils.ToSnakeCase(sortBy)
	logger.Debugf("Sorting by %v", snakeCasedSortBy)
	return fmt.Sprintf("%v %v", snakeCasedSortBy, sortDirection), nil
}
