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

import { ChangeEvent, forwardRef } from 'react';

import { ImportOptions } from '../../../../../core/projects/services/project-service.interface';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { mediaExtensionHandler } from '../../../../../providers/media-upload-provider/media-upload.validator';
import { useProjectsImportProvider } from '../../../../../providers/projects-import-provider/projects-import-provider.component';
import { isValidFileExtension } from '../../../../../shared/media-utils';

const VALID_EXTENSIONS = ['zip'];

export const ProjectImportFilePicker = forwardRef<HTMLInputElement, { options: ImportOptions }>(({ options }, ref) => {
    const { importProject } = useProjectsImportProvider();
    const { addNotification } = useNotification();

    const onFileInputChange = (event: ChangeEvent<HTMLInputElement>): void => {
        const file = event?.target.files?.[0];
        if (file && !isValidFileExtension(file, VALID_EXTENSIONS)) {
            addNotification({ message: 'Invalid file extension, please try again', type: NOTIFICATION_TYPE.ERROR });
            return;
        }

        importProject(file as File, options);
        event.target.value = '';
    };

    return (
        <input
            hidden
            type='file'
            multiple={false}
            ref={ref}
            id={'upload-project-file-id'}
            accept={mediaExtensionHandler(VALID_EXTENSIONS)}
            onChange={onFileInputChange}
            aria-label='upload-media-input'
            style={{ pointerEvents: 'all' }}
        />
    );
});
