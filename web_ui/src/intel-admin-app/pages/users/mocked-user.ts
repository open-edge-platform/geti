// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
export const MOCKED_USERS = [
    {
        id: '1',
        firstName: 'John',
        secondName: 'Doe',
        email: 'test@example.com',
    },
    {
        id: '2',
        firstName: 'Jane',
        secondName: 'Smith',
        email: 'test2@example.com',
    },
    {
        id: '3',
        firstName: 'Alice',
        secondName: 'Johnson',
        email: 'test3@example.com',
    },
    {
        id: '4',
        firstName: 'Bob',
        secondName: 'Brown',
        email: 'test4@example.com',
    },
    {
        id: '5',
        firstName: 'Charlie',
        secondName: 'Davis',
        email: 'test5@example.com',
    },
];

export type User = (typeof MOCKED_USERS)[number];
