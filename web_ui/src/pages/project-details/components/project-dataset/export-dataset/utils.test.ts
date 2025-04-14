// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ExportFormats } from '../../../../../core/projects/dataset.interface';
import { isDatumaroFormat } from './utils';

describe('project-dataset utils', () => {
    it('isDatumaroFormat', () => {
        expect(isDatumaroFormat(undefined)).toBe(false);
        expect(isDatumaroFormat(ExportFormats.COCO)).toBe(false);
        expect(isDatumaroFormat(ExportFormats.DATUMARO)).toBe(true);
    });
});
