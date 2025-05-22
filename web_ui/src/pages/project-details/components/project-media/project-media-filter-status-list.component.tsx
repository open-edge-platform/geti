// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';
import { AcceptSmall } from '@geti/ui/icons';
import { COLOR_MODE } from '@geti/ui/icons/color-mode.enum';

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
