// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
