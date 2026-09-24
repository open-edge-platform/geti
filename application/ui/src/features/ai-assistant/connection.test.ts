// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getAiConnection, setAiConnection } from './connection';

it('keeps the external-store snapshot stable until the connection changes', () => {
    const initial = getAiConnection();

    expect(getAiConnection()).toBe(initial);

    setAiConnection({ model: `${initial.model}-changed` });

    expect(getAiConnection()).not.toBe(initial);
    expect(getAiConnection()).toBe(getAiConnection());
});
