// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../labels/label.interface';

export interface LabeledVideoRange {
    start: number;
    end: number;
    labels: Label[];
}
