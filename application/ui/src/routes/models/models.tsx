// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isString } from 'lodash-es';

import { ExportJobsList } from '../../features/dataset/import-export/export-jobs-list/export-jobs-list.component';
import { ModelListingContainer } from '../../features/models/model-listing/model-listing.container';

export const Models = () => {
    return <ModelListingContainer exportJobs={<ExportJobsList predicate={({ datasetId }) => isString(datasetId)} />} />;
};
