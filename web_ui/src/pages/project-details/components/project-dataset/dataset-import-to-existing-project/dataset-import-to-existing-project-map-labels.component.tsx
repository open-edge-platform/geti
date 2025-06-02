// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { ActionButton, Flex, Text, TextField, Tooltip, TooltipTrigger, View, VisuallyHidden } from '@geti/ui';
import { Close } from '@geti/ui/icons';
import { isEmpty, omitBy, sortBy } from 'lodash-es';

import { DatasetImportToExistingProjectItem } from '../../../../../core/datasets/dataset.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { useDatasetImportToExistingProject } from '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { hasEqualId, runWhenTruthy } from '../../../../../shared/utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { LabelSearch } from '../../../../annotator/components/labels/label-search/label-search.component';

interface DatasetImportToExistingProjectMapLabelsProps {
    projectLabels: Label[];
    activeDatasetImport: DatasetImportToExistingProjectItem;
}

interface DatasetImportToExistingProjectMapLabelProps {
    projectLabels: Label[];
    mappingLabelName: string;
    selectedLabelId: string | undefined;
    onMappingChange: (mappedItem: Record<string, string>) => void;
    onMappingClear: (labelName: string) => void;
    testId: string;
}

const DatasetImportToExistingProjectMapLabel = ({
    projectLabels,
    mappingLabelName,
    selectedLabelId,
    onMappingChange,
    onMappingClear,
    testId,
}: DatasetImportToExistingProjectMapLabelProps) => {
    const selectedLabel = useMemo(
        () => projectLabels.find(hasEqualId(selectedLabelId)),
        [selectedLabelId, projectLabels]
    );

    return (
        <View
            height='size-600'
            paddingStart='size-200'
            paddingEnd='size-100'
            backgroundColor='gray-100'
            data-testid={testId}
        >
            <Flex gap='size-100' height='100%' justifyContent='space-between' alignItems='center'>
                <Flex alignItems='center' flex={1}>
                    <Text
                        id={idMatchingFormat(`existing-label-${mappingLabelName}-id`)}
                        data-testid={idMatchingFormat(`existing-label-${mappingLabelName}-id`)}
                    >
                        {mappingLabelName}
                    </Text>
                </Flex>
                <Flex alignItems='center' justifyContent='center' width='size-250'>
                    →
                </Flex>
                <Flex alignItems='center' flex={1}>
                    <View flexGrow={1}>
                        {selectedLabel && (
                            <View
                                id={idMatchingFormat(`target-label-${selectedLabel.name}-id`)}
                                data-testid={idMatchingFormat(`target-label-${selectedLabel.name}-id`)}
                            >
                                {selectedLabel.name}
                            </View>
                        )}
                        <View isHidden={selectedLabel !== undefined}>
                            <LabelSearch
                                id={mappingLabelName}
                                labels={projectLabels}
                                onClick={runWhenTruthy((label: Label) => {
                                    onMappingChange({ [mappingLabelName]: label.id });
                                })}
                                dontFocusOnMount
                                suffix={() => <></>}
                            />
                        </View>
                    </View>
                    {selectedLabel && (
                        <TooltipTrigger placement='right'>
                            <ActionButton
                                isQuiet
                                aria-label='clear-mapping-button'
                                onPress={() => onMappingClear(mappingLabelName)}
                            >
                                <Close width='16px' height='16px' />
                            </ActionButton>
                            <Tooltip>Clear mapping</Tooltip>
                        </TooltipTrigger>
                    )}
                </Flex>
            </Flex>
        </View>
    );
};

export const DatasetImportToExistingProjectMapLabels = ({
    projectLabels,
    activeDatasetImport,
}: DatasetImportToExistingProjectMapLabelsProps) => {
    const { patchActiveDatasetImport } = useDatasetImportToExistingProject();
    const { labels, labelsMap } = activeDatasetImport;
    const sortedLabels = sortBy(labels, (label) => label);
    const NO_LABELS_INFORMATION = 'No labels were detected in the dataset. Only images will be imported.';

    const noLabelsInMatchingStep = isEmpty(labels);

    const onMappingChange = (mappedItem: Record<string, string>): void => {
        patchActiveDatasetImport({ labelsMap: { ...labelsMap, ...mappedItem } });
    };

    const onMappingClear = (labelName: string): void => {
        patchActiveDatasetImport({ labelsMap: omitBy(labelsMap, (_, key) => key === labelName) });
    };

    if (noLabelsInMatchingStep) {
        return <Text>{NO_LABELS_INFORMATION}</Text>;
    }

    return (
        <div aria-label='dataset-import-to-existing-project-map-labels'>
            <Flex marginBottom='size-250' gap='size-400' justifyContent='space-between' alignItems='center'>
                <Text id='dataset-import-to-existing-project-existing-labels' flex={1}>
                    Existing labels
                </Text>
                <Text id='dataset-import-to-existing-project-target-labels' flex={1}>
                    Target labels
                </Text>
            </Flex>
            <VisuallyHidden>
                {/* We're using this field to prevent a weird focus bug when the user
                    closes a label search component this text field will be focused instead of
                    another label search input, preventing a results panel to be opened */}
                <TextField aria-label='This text field is unused' />
            </VisuallyHidden>
            <Flex gap='size-10' direction='column'>
                {sortedLabels.map((mappingLabelName: string, index: number) => (
                    <DatasetImportToExistingProjectMapLabel
                        testId={`label-mapping-${index}`}
                        key={`${mappingLabelName}-${index}`}
                        mappingLabelName={mappingLabelName}
                        projectLabels={projectLabels}
                        selectedLabelId={labelsMap[mappingLabelName]}
                        onMappingChange={onMappingChange}
                        onMappingClear={onMappingClear}
                    />
                ))}
            </Flex>
        </div>
    );
};
