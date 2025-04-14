// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ResponseTotalsDTO } from '../../dtos/credits.interface';
import { CreditServiceName, TransactionsAggregatesKey } from '../transactions.interface';

export interface TransactionsResponseDTO extends ResponseTotalsDTO {
    transactions: {
        credits: number;
        workspace_id: string;
        project_id: string;
        service_name: CreditServiceName;
        milliseconds_timestamp: number;
    }[];
}

export interface TransactionsAggregatesDTO extends ResponseTotalsDTO {
    aggregates: {
        group: {
            key: TransactionsAggregatesKey;
            value: string;
        }[];
        result: {
            credits: number;
            resources: {
                [key: string]: number | undefined;
            };
        };
    }[];
}
