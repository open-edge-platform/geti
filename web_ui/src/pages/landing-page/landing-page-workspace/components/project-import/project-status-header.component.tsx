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

import { ReactNode } from 'react';

import { Divider, Flex, Heading } from '@adobe/react-spectrum';

import { getFileSize } from '../../../../../shared/utils';

import classes from './project-import.module.scss';

interface ProjectStatusHeaderProps {
    fileName: string;
    fileSize: number;
    menuActions?: ReactNode;
}

export const ProjectStatusHeader = ({ fileName, fileSize, menuActions }: ProjectStatusHeaderProps): JSX.Element => {
    return (
        <>
            <Flex>
                <Heading level={6} UNSAFE_className={classes.statusTitle}>
                    Project creation - {fileName} - {getFileSize(fileSize)}
                </Heading>
                {menuActions}
            </Flex>
            <Divider size='S' marginTop={'size-150'} marginBottom={'size-200'} />
        </>
    );
};
