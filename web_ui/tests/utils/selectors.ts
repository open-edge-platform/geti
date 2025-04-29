// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

export const getSubmitButton = (page: Page) => page.locator('#secondary-toolbar-submit');

export const getAnnotationListItems = (page: Page) => page.getByRole('listitem', { name: /Annotation with id .*/i });
