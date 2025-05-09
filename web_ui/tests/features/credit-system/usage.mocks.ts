// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { range } from 'lodash-es';

export const mockedOrganizationBalance = {
    incoming: 100,
    available: 30,
};

export const mockedCreditAccountsFew = {
    total_matched: 2,
    next_page: null,
    credit_accounts: [
        {
            id: 34,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Freemium credits',
            renewable_amount: 100,
            renewal_day_of_month: 30,
            created: 1714468347222,
            updated: 1714468347222,
            expires: null,
            balance: {
                incoming: 100,
                available: 1000,
            },
        },
        {
            id: 33,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Welcoming Credits',
            renewable_amount: 0,
            renewal_day_of_month: null,
            created: 1714468347215,
            updated: 1714468347215,
            expires: 1717060347215,
            balance: {
                incoming: 100,
                available: 1000,
            },
        },
    ],
};

export const mockedCreditAccountsMany = {
    total_matched: 5,
    next_page: null,
    credit_accounts: [
        {
            id: 34,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Freemium credits',
            renewable_amount: 100,
            renewal_day_of_month: 30,
            created: 1714468347222,
            updated: 1714468347222,
            expires: null,
            balance: {
                incoming: 0,
                available: 0,
            },
        },
        {
            id: 33,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Welcoming Credits 1',
            renewable_amount: 0,
            renewal_day_of_month: null,
            created: 1714468347215,
            updated: 1714468347215,
            expires: 1717060347215,
            balance: {
                incoming: 1000,
                available: 1000,
            },
        },
        {
            id: 32,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Welcoming Credits 2',
            renewable_amount: 0,
            renewal_day_of_month: null,
            created: 1714468347215,
            updated: 1714468347215,
            expires: null,
            balance: {
                incoming: 0,
                available: 0,
            },
        },
        {
            id: 31,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Welcoming Credits 3',
            renewable_amount: 0,
            renewal_day_of_month: null,
            created: 1714468347215,
            updated: 1714468347215,
            expires: null,
            balance: {
                incoming: 0,
                available: 0,
            },
        },
        {
            id: 30,
            organization_id: '590a6bab-33f8-4530-9a78-f57abaca5851',
            name: 'Welcoming Credits 5',
            renewable_amount: 0,
            renewal_day_of_month: null,
            created: 1714468347215,
            updated: 1714468347215,
            expires: null,
            balance: {
                incoming: 0,
                available: 0,
            },
        },
    ],
};

export const mockedMonthlyCreditConsumptionAggregation = {
    aggregates: [
        {
            group: [
                {
                    key: 'project',
                    value: 'project_id_1',
                },
            ],
            result: {
                credits: 30,
                resources: {
                    images: 30,
                    frames: 0,
                },
            },
        },
        {
            group: [
                {
                    key: 'project',
                    value: 'project_id_1',
                },
            ],
            result: {
                credits: 350,
                resources: {
                    images: 100,
                    frames: 250,
                },
            },
        },
        {
            group: [
                {
                    key: 'project',
                    value: 'project_id_2',
                },
            ],
            result: {
                credits: 112,
                resources: {
                    images: 0,
                    frames: 112,
                },
            },
        },
        {
            group: [
                {
                    key: 'project',
                    value: 'project_id_2',
                },
            ],
            result: {
                credits: 77,
                resources: {
                    images: 77,
                    frames: 0,
                },
            },
        },
    ],
};

export const getMockedProjectAggregatesByTime = (time?: number | null) => {
    if (time && Number.parseInt(`${time}`) > new Date('2024-03-15').valueOf()) {
        return {
            aggregates: [
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_1',
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 100,
                        resources: {
                            images: 100,
                            frames: 0,
                        },
                    },
                },
            ],
        };
    } else if (Number.parseInt(`${time}`) <= new Date('2024-03-15').valueOf()) {
        return {
            aggregates: [
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_1',
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 201,
                        resources: {
                            images: 201,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_2',
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 202,
                        resources: {
                            images: 202,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_2',
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 103,
                        resources: {
                            images: 103,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_3',
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 104,
                        resources: {
                            images: 104,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_4',
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 105,
                        resources: {
                            images: 105,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_5',
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 106,
                        resources: {
                            images: 106,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_6',
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 107,
                        resources: {
                            images: 107,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'project',
                            value: 'project_id_7',
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 108,
                        resources: {
                            images: 108,
                            frames: 0,
                        },
                    },
                },
            ],
        };
    } else {
        return {
            aggregates: [],
        };
    }
};

export const mockedProjects = {
    projects: [
        {
            id: 'project_id_1',
            name: 'Project 1',
            pipeline: { tasks: [] },
            performance: {
                score: null,
                task_performances: [],
            },
            storage_info: {},
            thumbnail:
                // eslint-disable-next-line max-len
                '/api/v1/organizations/80d0d079-b261-4c09-bcdc-0672852bfb7c/workspaces/f9a7a4c7-6d64-4672-ab8e-78f9b96aed74/projects/project_id_1/thumbnail',
        },
        {
            id: 'project_id_2',
            name: 'Project 2',
            pipeline: { tasks: [] },
            performance: {
                score: null,
                task_performances: [],
            },
            storage_info: {},
            thumbnail:
                // eslint-disable-next-line max-len
                '/api/v1/organizations/80d0d079-b261-4c09-bcdc-0672852bfb7c/workspaces/f9a7a4c7-6d64-4672-ab8e-78f9b96aed74/projects/project_id_2/thumbnail',
        },
        {
            id: 'project_id_3',
            name: 'Project 3',
            pipeline: { tasks: [] },
            performance: {
                score: null,
                task_performances: [],
            },
            storage_info: {},
            thumbnail:
                // eslint-disable-next-line max-len
                '/api/v1/organizations/80d0d079-b261-4c09-bcdc-0672852bfb7c/workspaces/f9a7a4c7-6d64-4672-ab8e-78f9b96aed74/projects/project_id_3/thumbnail',
        },
    ],
};

export const getMockedTimeAggregates = (projectId: string[] | null | undefined) => {
    if (projectId?.includes('project_id_1')) {
        return {
            aggregates: [
                {
                    group: [
                        {
                            key: 'date',
                            value: new Date('2024-04-15').valueOf(),
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 50,
                        resources: {
                            images: 50,
                            frames: 0,
                        },
                    },
                },
            ],
        };
    } else {
        return {
            aggregates: [
                {
                    group: [
                        {
                            key: 'date',
                            value: new Date('2024-04-10').valueOf(),
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 100,
                        resources: {
                            images: 100,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'date',
                            value: new Date('2024-04-11').valueOf(),
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 150,
                        resources: {
                            images: 150,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'date',
                            value: new Date('2024-04-15').valueOf(),
                        },
                        {
                            key: 'service_name',
                            value: 'optimization',
                        },
                    ],
                    result: {
                        credits: 100,
                        resources: {
                            images: 100,
                            frames: 0,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: 'date',
                            value: new Date('2024-04-15').valueOf(),
                        },
                        {
                            key: 'service_name',
                            value: 'training',
                        },
                    ],
                    result: {
                        credits: 100,
                        resources: {
                            images: 100,
                            frames: 0,
                        },
                    },
                },
            ],
        };
    }
};

export const mockedProjectNames = {
    projects: range(1, 3).map((idx) => ({
        name: `Project ${idx}`,
        id: `project_id_${idx}`,
    })),
};
