// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Tag } from '@geti/ui';

import { idMatchingFormat } from '../../../../../test-utils/id-utils';

interface PreselectedModelProps {
    taskName: string;
    modelGroupName: string;
    modelVersion: string;
    optimizationModelName?: string;
}

export const PreselectedModelInfo = ({
    taskName,
    modelGroupName,
    modelVersion,
    optimizationModelName,
}: PreselectedModelProps): JSX.Element => {
    const items = [taskName, modelGroupName, modelVersion];

    if (optimizationModelName) {
        items.push(optimizationModelName);
    }

    return (
        <>
            <Flex gap={'size-100'} wrap id={'preselected-info-id'}>
                {items.map((item) => (
                    <Tag id={`${idMatchingFormat(item)}-id`} text={item} key={idMatchingFormat(item)} withDot={false} />
                ))}
            </Flex>
            <Divider size={'M'} />
        </>
    );
};
