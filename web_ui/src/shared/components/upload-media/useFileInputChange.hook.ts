// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ChangeEvent } from 'react';

import isEmpty from 'lodash/isEmpty';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { EMPTY_FOLDER_WARNING_MESSAGE } from '../../custom-notification-messages';

interface UseOnFileInputChangeProps {
    uploadCallback: (files: File[]) => void;
}

interface UseOnFileInputChange {
    onFileInputChange: (event: ChangeEvent<HTMLInputElement>) => void;
}

const isFile = (value: unknown): value is File => value instanceof File;

export const useOnFileInputChange = ({ uploadCallback }: UseOnFileInputChangeProps): UseOnFileInputChange => {
    const { addNotification } = useNotification();

    const onFileInputChange = (event: ChangeEvent<HTMLInputElement>): void => {
        const fileList = event.target.files;

        if (!fileList) return;

        const filteredFileList = Object.values(fileList).filter(isFile);

        if (isEmpty(filteredFileList)) {
            addNotification({ message: EMPTY_FOLDER_WARNING_MESSAGE, type: NOTIFICATION_TYPE.DEFAULT });
        } else {
            uploadCallback(filteredFileList);
        }

        // After all the logic we want to clear the value.
        // This changes nothing for the frontend, but it avoids a bigger effort for the validation team
        event.target.value = '';
    };

    return {
        onFileInputChange,
    };
};
