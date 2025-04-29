// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { MEDIA_CONTENT_BUCKET } from '../../../src/providers/media-upload-provider/media-upload.interface';
import { ProjectMediaBucketPage } from './project-media-bucket-page';

export class ProjectMediaPage {
    constructor(private page: Page) {}

    async getBucket(bucket: MEDIA_CONTENT_BUCKET = MEDIA_CONTENT_BUCKET.GENERIC): Promise<ProjectMediaBucketPage> {
        return new ProjectMediaBucketPage(this.page, this.page.getByTestId(`${bucket.toLocaleLowerCase()}-content-id`));
    }
}
