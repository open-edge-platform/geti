// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestUserHasRequiredRoles(t *testing.T) {
	userRoles := []string{"role1", "role2", "role3"}
	requiredRoles := []string{"role1", "role2"}

	assert.True(t, UserHasRequiredRoles(userRoles, requiredRoles))

	requiredRoles = []string{"role1", "role4"}
	assert.False(t, UserHasRequiredRoles(userRoles, requiredRoles))
}
