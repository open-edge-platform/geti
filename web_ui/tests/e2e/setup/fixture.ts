// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { testWithLocalStorageState } from '../../fixtures/open-api';
import { test } from '../fixtures';

// Reset localstorage and cookie state so that we can login
export const setup = testWithLocalStorageState(test, async () => []);
