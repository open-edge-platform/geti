// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ModelIdentifier } from '../../models/models.interface';
import { TrainingModelStatistic } from '../model-statistics.interface';
import { ApiModelStatisticsServiceInterface } from './api-model-statistics-service';

export const createInMemoryModelStatisticsService = (): ApiModelStatisticsServiceInterface => {
    const getModelStatistics = async (_modelIdentifier: ModelIdentifier): Promise<TrainingModelStatistic[]> => {
        const data: TrainingModelStatistic[] = [
            {
                value: '2021-07-05T12:01:02.162000+00:00',
                header: 'Training date',
                key: 'training-date',
                type: 'text',
            },
            {
                value: '01:22:44',
                header: 'Training duration',
                key: 'training-duration',
                type: 'text',
            },
            {
                value: [
                    {
                        header: 'validation',
                        key: 'validation',
                        color: '#888888',
                        value: 0.84 * 100,
                    },
                    {
                        header: 'test',
                        key: 'number',
                        color: '#FF5662',
                        value: 0.86 * 100,
                    },
                ],
                header: 'Dice average',
                key: 'dice-average',
                type: 'radial_bar',
            },
            {
                value: [
                    {
                        header: 'awerty',
                        key: 'awerty',
                        color: '#FF5662',
                        value: 0.84,
                    },
                    {
                        header: 'Testing123',
                        key: 'Testing123',
                        color: '#888888',
                        value: 0.75,
                    },
                ],
                header: 'Dice Average Per Label (validation)',
                key: 'dice-average-per-label-(validation)',
                type: 'bar',
            },
            {
                value: {
                    lineData: [
                        {
                            color: '#888888',
                            header: 'Training',
                            key: 'Training',
                            points: [
                                {
                                    x: 1,
                                    y: 0.5457000136375427,
                                },
                                {
                                    x: 2,
                                    y: 0.5699999928474426,
                                },
                                {
                                    x: 3,
                                    y: 0.541700005531311,
                                },
                                {
                                    x: 4,
                                    y: 0.5406000018119812,
                                },
                                {
                                    x: 5,
                                    y: 0.5394999980926514,
                                },
                                {
                                    x: 6,
                                    y: 0.5371000170707703,
                                },
                                {
                                    x: 7,
                                    y: 0.5314000248908997,
                                },
                                {
                                    x: 8,
                                    y: 0.5275999903678894,
                                },
                                {
                                    x: 9,
                                    y: 0.5252000093460083,
                                },
                                {
                                    x: 10,
                                    y: 0.5209000110626221,
                                },
                                {
                                    x: 11,
                                    y: 0.517300009727478,
                                },
                                {
                                    x: 12,
                                    y: 0.522599995136261,
                                },
                                {
                                    x: 13,
                                    y: 0.510699987411499,
                                },
                                {
                                    x: 14,
                                    y: 0.5073999762535095,
                                },
                                {
                                    x: 15,
                                    y: 0.5055000185966492,
                                },
                                {
                                    x: 16,
                                    y: 0.5019999742507935,
                                },
                                {
                                    x: 17,
                                    y: 0.49959999322891235,
                                },
                                {
                                    x: 18,
                                    y: 0.49709999561309814,
                                },
                                {
                                    x: 19,
                                    y: 0.4893999993801117,
                                },
                                {
                                    x: 20,
                                    y: 0.4875999987125397,
                                },
                                {
                                    x: 21,
                                    y: 0.4837000072002411,
                                },
                                {
                                    x: 22,
                                    y: 0.47699999809265137,
                                },
                                {
                                    x: 23,
                                    y: 0.4745999872684479,
                                },
                                {
                                    x: 24,
                                    y: 0.4672999978065491,
                                },
                                {
                                    x: 25,
                                    y: 0.46889999508857727,
                                },
                                {
                                    x: 26,
                                    y: 0.4648999869823456,
                                },
                                {
                                    x: 27,
                                    y: 0.4702000021934509,
                                },
                                {
                                    x: 28,
                                    y: 0.4571000039577484,
                                },
                                {
                                    x: 29,
                                    y: 0.4535999894142151,
                                },
                                {
                                    x: 30,
                                    y: 0.4505999982357025,
                                },
                                {
                                    x: 31,
                                    y: 0.44859999418258667,
                                },
                                {
                                    x: 32,
                                    y: 0.4426000118255615,
                                },
                                {
                                    x: 33,
                                    y: 0.4453999996185303,
                                },
                                {
                                    x: 34,
                                    y: 0.4397999942302704,
                                },
                                {
                                    x: 35,
                                    y: 0.4311000108718872,
                                },
                                {
                                    x: 36,
                                    y: 0.42559999227523804,
                                },
                                {
                                    x: 37,
                                    y: 0.42289999127388,
                                },
                                {
                                    x: 38,
                                    y: 0.4185999929904938,
                                },
                                {
                                    x: 39,
                                    y: 0.4214000105857849,
                                },
                                {
                                    x: 40,
                                    y: 0.41990000009536743,
                                },
                            ],
                        },
                        {
                            color: '#FF5662',
                            header: 'Validation',
                            key: 'validation',
                            points: [
                                {
                                    x: 1,
                                    y: 0.5625,
                                },
                                {
                                    x: 2,
                                    y: 0.5370000004768372,
                                },
                                {
                                    x: 3,
                                    y: 0.5365999937057495,
                                },
                                {
                                    x: 4,
                                    y: 0.5357999801635742,
                                },
                                {
                                    x: 5,
                                    y: 0.5321000218391418,
                                },
                                {
                                    x: 6,
                                    y: 0.5275999903678894,
                                },
                                {
                                    x: 7,
                                    y: 0.5245000123977661,
                                },
                                {
                                    x: 8,
                                    y: 0.5220999717712402,
                                },
                                {
                                    x: 9,
                                    y: 0.5195000171661377,
                                },
                                {
                                    x: 10,
                                    y: 0.5156999826431274,
                                },
                                {
                                    x: 11,
                                    y: 0.5144000053405762,
                                },
                                {
                                    x: 12,
                                    y: 0.5083000063896179,
                                },
                                {
                                    x: 13,
                                    y: 0.504800021648407,
                                },
                                {
                                    x: 14,
                                    y: 0.5012000203132629,
                                },
                                {
                                    x: 15,
                                    y: 0.4973999857902527,
                                },
                                {
                                    x: 16,
                                    y: 0.49380001425743103,
                                },
                                {
                                    x: 17,
                                    y: 0.4902999997138977,
                                },
                                {
                                    x: 18,
                                    y: 0.48660001158714294,
                                },
                                {
                                    x: 19,
                                    y: 0.4828999936580658,
                                },
                                {
                                    x: 20,
                                    y: 0.47929999232292175,
                                },
                                {
                                    x: 21,
                                    y: 0.475600004196167,
                                },
                                {
                                    x: 22,
                                    y: 0.4715999960899353,
                                },
                                {
                                    x: 23,
                                    y: 0.4675000011920929,
                                },
                                {
                                    x: 24,
                                    y: 0.4634000062942505,
                                },
                                {
                                    x: 25,
                                    y: 0.4593000113964081,
                                },
                                {
                                    x: 26,
                                    y: 0.4553000032901764,
                                },
                                {
                                    x: 27,
                                    y: 0.45170000195503235,
                                },
                                {
                                    x: 28,
                                    y: 0.44830000400543213,
                                },
                                {
                                    x: 29,
                                    y: 0.4447999894618988,
                                },
                                {
                                    x: 30,
                                    y: 0.4410000145435333,
                                },
                                {
                                    x: 31,
                                    y: 0.43720000982284546,
                                },
                                {
                                    x: 32,
                                    y: 0.43320000171661377,
                                },
                                {
                                    x: 33,
                                    y: 0.4293000102043152,
                                },
                                {
                                    x: 34,
                                    y: 0.42559999227523804,
                                },
                                {
                                    x: 35,
                                    y: 0.42179998755455017,
                                },
                                {
                                    x: 36,
                                    y: 0.4180999994277954,
                                },
                                {
                                    x: 37,
                                    y: 0.4275999963283539,
                                },
                                {
                                    x: 38,
                                    y: 0.4104999899864197,
                                },
                                {
                                    x: 39,
                                    y: 0.4068000018596649,
                                },
                                {
                                    x: 40,
                                    y: 0.40380001068115234,
                                },
                            ],
                        },
                    ],
                    xAxisLabel: 'Epoch',
                    yAxisLabel: 'train/loss_bbox',
                },
                header: 'Loss curve',
                key: 'loss-curve',
                type: 'line',
            },
            {
                value: {
                    lineData: [
                        {
                            color: '#888888',
                            header: 'Validation',
                            key: 'validation',
                            points: [
                                {
                                    x: 1,
                                    y: 0.015,
                                },
                                {
                                    x: 2,
                                    y: 0.649,
                                },
                                {
                                    x: 3,
                                    y: 0.137,
                                },
                                {
                                    x: 4,
                                    y: 0.15,
                                },
                                {
                                    x: 5,
                                    y: 0.295,
                                },
                                {
                                    x: 6,
                                    y: 0.693,
                                },
                                {
                                    x: 7,
                                    y: 0.798,
                                },
                                {
                                    x: 8,
                                    y: 0.8,
                                },
                                {
                                    x: 9,
                                    y: 0.791,
                                },
                                {
                                    x: 10,
                                    y: 0.777,
                                },
                                {
                                    x: 11,
                                    y: 0.555,
                                },
                                {
                                    x: 12,
                                    y: 0.792,
                                },
                                {
                                    x: 13,
                                    y: 0.82,
                                },
                                {
                                    x: 14,
                                    y: 0.838,
                                },
                                {
                                    x: 15,
                                    y: 0.834,
                                },
                                {
                                    x: 16,
                                    y: 0.816,
                                },
                                {
                                    x: 17,
                                    y: 0.803,
                                },
                                {
                                    x: 18,
                                    y: 0.798,
                                },
                                {
                                    x: 19,
                                    y: 0.802,
                                },
                                {
                                    x: 20,
                                    y: 0.806,
                                },
                                {
                                    x: 21,
                                    y: 0.812,
                                },
                                {
                                    x: 22,
                                    y: 0.813,
                                },
                                {
                                    x: 23,
                                    y: 0.814,
                                },
                                {
                                    x: 24,
                                    y: 0.811,
                                },
                                {
                                    x: 25,
                                    y: 0.804,
                                },
                                {
                                    x: 26,
                                    y: 0.809,
                                },
                                {
                                    x: 27,
                                    y: 0.821,
                                },
                                {
                                    x: 28,
                                    y: 0.83,
                                },
                                {
                                    x: 29,
                                    y: 0.834,
                                },
                                {
                                    x: 30,
                                    y: 0.829,
                                },
                                {
                                    x: 31,
                                    y: 0.826,
                                },
                                {
                                    x: 32,
                                    y: 0.826,
                                },
                                {
                                    x: 33,
                                    y: 0.83,
                                },
                                {
                                    x: 34,
                                    y: 0.833,
                                },
                                {
                                    x: 35,
                                    y: 0.838,
                                },
                                {
                                    x: 36,
                                    y: 0.825,
                                },
                                {
                                    x: 37,
                                    y: 0.639,
                                },
                                {
                                    x: 38,
                                    y: 0.832,
                                },
                                {
                                    x: 39,
                                    y: 0.852,
                                },
                                {
                                    x: 40,
                                    y: 0.867,
                                },
                            ],
                        },
                    ],
                    xAxisLabel: 'Epoch',
                    yAxisLabel: 'train/loss_bbox',
                },
                header: 'Dice curve',
                key: 'dice-curve',
                type: 'line',
            },
            {
                header: 'Confusion matrix',
                key: 'Confusion matrix',
                type: 'matrix',
                value: {
                    columnHeader: 'True label',
                    matrixData: [
                        {
                            columnNames: ['Background', 'label1'],
                            header: 'Confusion matrix (Validation)',
                            key: 'Confusion matrix (Validation)',
                            matrixValues: [
                                [0.9395321011543274, 0.0604679211974144],
                                [0.17742396891117096, 0.8225760459899902],
                            ],
                            rowNames: ['Background', 'label1'],
                        },
                        {
                            columnNames: ['Background', 'Background2', 'awerty'],
                            header: 'Confusion matrix (Training)',
                            key: 'confusion-matrix-(training)',
                            matrixValues: [
                                [0.32, 0.32, 0.36],
                                [0.02473498322069645, 0.9752650260925293, 0.699123412],
                                [0.42473498322069645, 0.4952650260925293, 0.899123412],
                            ],
                            rowNames: ['Background', 'Background2', 'awerty'],
                        },
                        {
                            columnNames: [
                                'Background',
                                'Background2',
                                'Background3',
                                'Background4',
                                'Background5',
                                'Background6',
                                'awerty',
                            ],
                            header: 'Confusion matrix2 (Training)',
                            key: 'confusion-matrix2-(Training)',
                            matrixValues: [
                                [
                                    0.9993090629577637, 0.000690929067786783, 0.35523123123, 0.9993090629577637,
                                    0.000690929067786783, 0.35523123123, 0.000690929067786783,
                                ],
                                [
                                    0.02473498322069645, 0.9752650260925293, 0.699123412, 0.02473498322069645,
                                    0.9752650260925293, 0.699123412, 0.699123412,
                                ],
                                [
                                    0.42473498322069645, 0.4952650260925293, 0.899123412, 0.42473498322069645,
                                    0.4952650260925293, 0.899123412, 0.899123412,
                                ],
                                [
                                    0.9993090629577637, 0.000690929067786783, 0.35523123123, 0.9993090629577637,
                                    0.000690929067786783, 0.35523123123, 0.000690929067786783,
                                ],
                                [
                                    0.02473498322069645, 0.9752650260925293, 0.699123412, 0.02473498322069645,
                                    0.9752650260925293, 0.9752650260925293, 0.699123412,
                                ],
                                [
                                    0.42473498322069645, 0.4952650260925293, 0.899123412, 0.42473498322069645,
                                    0.4952650260925293, 0.899123412, 0.899123412,
                                ],
                                [
                                    0.42473498322069645, 0.4952650260925293, 0.899123412, 0.42473498322069645,
                                    0.4952650260925293, 0.129123412, 0.69,
                                ],
                            ],
                            rowNames: [
                                'Background',
                                'Background2',
                                'Background3',
                                'Background4',
                                'Background5',
                                'Background6',
                                'awerty',
                            ],
                        },
                    ],
                    rowHeader: 'Predicted label',
                },
            },
        ];
        return Promise.resolve(data);
    };

    return { getModelStatistics };
};
