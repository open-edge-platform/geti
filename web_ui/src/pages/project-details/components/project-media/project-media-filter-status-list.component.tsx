// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';

import { AcceptSmall } from '../../../../assets/icons';
import { COLOR_MODE } from '../../../../assets/icons/color-mode.enum';
import { useProject } from '../../providers/project-provider/project-provider.component';

interface StatusItem {
    key: string;
    name: string;
    isVisible: boolean;
}

interface ProjectMediaAnnotationStatusListProps {
    selected?: string;
    onSelectionChange: (key: string) => void;
}

export const ProjectMediaFilterStatusList = ({
    selected,
    onSelectionChange,
}: ProjectMediaAnnotationStatusListProps): JSX.Element => {
    const { isTaskChainProject } = useProject();

    const statusList: StatusItem[] = [
        { key: '', name: 'Any', isVisible: true },
        { key: 'annotated', name: 'Annotated', isVisible: true },
        { key: 'partially_annotated', name: 'Partially Annotated', isVisible: isTaskChainProject },
        { key: 'none', name: 'None', isVisible: true },
    ];

    return (
        <>
            {statusList
                .filter(({ isVisible }) => isVisible)
                .map((statusItem: StatusItem) => (
                    <Flex key={`status-${statusItem.key}`} alignItems='center' marginY='size-50'>
                        <span
                            style={{ width: '100%', cursor: selected === statusItem.key ? 'default' : 'pointer' }}
                            id={statusItem.key || statusItem.name.toLowerCase()}
                            onClick={() => {
                                if (selected === statusItem.key) return;
                                onSelectionChange(statusItem.key);
                            }}
                        >
                            {statusItem.name}
                        </span>
                        {selected === statusItem.key ? <AcceptSmall color={COLOR_MODE.INFORMATIVE} /> : <></>}
                    </Flex>
                ))}
        </>
    );
};
