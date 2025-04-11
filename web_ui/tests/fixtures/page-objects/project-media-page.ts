// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Page } from '@playwright/test';

import { MEDIA_CONTENT_BUCKET } from '../../../src/providers/media-upload-provider/media-upload.interface';
import { ProjectMediaBucketPage } from './project-media-bucket-page';

export class ProjectMediaPage {
    constructor(private page: Page) {}

    async getBucket(bucket: MEDIA_CONTENT_BUCKET = MEDIA_CONTENT_BUCKET.GENERIC): Promise<ProjectMediaBucketPage> {
        return new ProjectMediaBucketPage(this.page, this.page.getByTestId(`${bucket.toLocaleLowerCase()}-content-id`));
    }
}
