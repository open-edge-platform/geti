// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
