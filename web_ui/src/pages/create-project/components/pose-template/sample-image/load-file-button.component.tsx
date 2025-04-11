// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FileTrigger, Flex } from '@adobe/react-spectrum';

import { Image } from '../../../../../assets/icons';
import { Button } from '../../../../../shared/components/button/button.component';
import { onValidFileList } from '../../../../../shared/utils';

interface LoadFileButtonProps {
    onFileLoaded: (image: string) => void;
}

export const LoadFileButton = ({ onFileLoaded }: LoadFileButtonProps) => {
    const onProcessUploadFile = onValidFileList(async ([file]: File[]) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            onFileLoaded(String(reader.result));
        };
        reader.readAsDataURL(file);
    });

    return (
        <FileTrigger onSelect={onProcessUploadFile} aria-label='upload sample image'>
            <Button variant={'secondary'} maxWidth={'size-3000'}>
                <Flex gap={'size-75'} alignItems={'center'}>
                    <Image />
                    Upload sample image
                </Flex>
            </Button>
        </FileTrigger>
    );
};
