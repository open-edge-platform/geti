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

import { useCallback, useMemo, useState } from 'react';

import { Flex, Heading, IllustratedMessage, Text, View } from '@adobe/react-spectrum';
import NotFound from '@spectrum-icons/illustrations/NotFound';
import differenceBy from 'lodash/differenceBy';
import intersectionBy from 'lodash/intersectionBy';
import isEmpty from 'lodash/isEmpty';
import uniqBy from 'lodash/uniqBy';

import { ChevronRightSmallLight, LabelGroup } from '../../../../../assets/icons';
import { DATASET_IMPORT_TASK_TYPE } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportLabel, DatasetImportToNewProjectItem } from '../../../../../core/datasets/dataset.interface';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { Checkbox } from '../../../../../shared/components/checkbox/checkbox.component';
import { Divider } from '../../../../../shared/components/divider/divider.component';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { ColorPickerDialog } from '../../../../create-project/components/project-labels-management/task-labels-management/color-picker-dialog.component';
import { getLabelFullPath, getLabelsStructureFromPaths, isTaskChainedProject } from './utils';

import classes from './dataset-import-to-new-project.module.scss';

interface BuildTreeProps {
    obj: Record<string, unknown>;
    disabled?: boolean;
    labelsInitiallyCollapsed?: boolean;
    isLabelSelected: (labelName: string) => boolean;
    isLabelIndeterminate: (labelName: string) => boolean;
    onToggleLabelSelection: (labelName: string) => void;
    labelColorMapSnapshot: Record<string, string>;
    onColorChange: (name: string) => (newColor: string) => void;
}

interface DatasetImportToNewProjectLabelsProps {
    datasetImportItem: DatasetImportToNewProjectItem;
    patchDatasetImport: (item: Partial<DatasetImportToNewProjectItem>) => void;
    labelsInitiallyCollapsed?: boolean;
}

const getTaskChainFirstTaskPaths = (firstChainLabels: DatasetImportLabel[], labelsToSelect: DatasetImportLabel[]) => {
    const firstChainPaths: string[] = []; // Paths for first task if project is task-chained
    const paths: string[] = [];

    firstChainLabels.forEach((firstChainLabel: DatasetImportLabel) =>
        firstChainPaths.push(getLabelFullPath(firstChainLabel.name, firstChainLabels))
    );

    labelsToSelect.forEach((otherLabel: DatasetImportLabel) =>
        paths.push(getLabelFullPath(otherLabel.name, labelsToSelect))
    );

    return {
        paths,
        firstChainPaths,
    };
};

const getPaths = (
    taskType: DATASET_IMPORT_TASK_TYPE | null,
    firstChainLabels: DatasetImportLabel[],
    labelsToSelect: DatasetImportLabel[]
) => {
    if (taskType === null) {
        return { paths: [], firstChainPaths: [] };
    }

    if (isTaskChainedProject(taskType)) {
        return getTaskChainFirstTaskPaths(firstChainLabels, labelsToSelect);
    }

    const paths: string[] = [];

    labelsToSelect.forEach((label: DatasetImportLabel) => paths.push(getLabelFullPath(label.name, labelsToSelect)));

    return { paths, firstChainPaths: [] };
};

const BuildTree = ({
    obj,
    disabled,
    labelsInitiallyCollapsed,
    isLabelSelected,
    onToggleLabelSelection,
    isLabelIndeterminate,
    labelColorMapSnapshot,
    onColorChange,
}: BuildTreeProps): JSX.Element => {
    const [isHidden, setIsHidden] = useState(labelsInitiallyCollapsed);

    const name: string = (obj.label ?? obj.group) as string;
    const children: Record<string, unknown>[] = obj.children as Record<string, unknown>[];

    const uid: string = idMatchingFormat(name);

    return (
        <li
            role='treeitem'
            aria-selected={isLabelSelected(name)}
            id={`treeitem-label-${uid}`}
            key={`treeitem-label-${uid}`}
        >
            <View
                paddingStart={isEmpty(children) ? 'size-200' : 'size-100'}
                paddingEnd='size-200'
                UNSAFE_className={classes.treeItem}
            >
                <Flex alignItems='center' height='100%' gap='size-100'>
                    {!isEmpty(children) && (
                        <ActionButton
                            isQuiet
                            aria-expanded={!isHidden}
                            onPress={() => setIsHidden(!isHidden)}
                            key={`expand-collapse-button-${uid}`}
                            id={`expand-collapse-button-${uid}`}
                            data-testid={`expand-collapse-button-${uid}`}
                            UNSAFE_className={classes.toggleExpandButton}
                        >
                            <ChevronRightSmallLight />
                        </ActionButton>
                    )}
                    {!!obj.label && (
                        <Checkbox
                            id={`select-${uid}-label`}
                            aria-label={`select-${uid}-label`}
                            isDisabled={disabled}
                            isSelected={isLabelSelected(name)}
                            isIndeterminate={isLabelIndeterminate(name)}
                            onChange={() => onToggleLabelSelection(name)}
                            UNSAFE_style={{ paddingRight: 0 }}
                        />
                    )}
                    <Flex alignItems='center' gap='size-200' marginStart={!!obj.label ? 'size-100' : 0}>
                        {!!obj.label ? (
                            <ColorPickerDialog
                                id={`change-color-button-${uid}`}
                                data-testid={`change-color-button-${uid}`}
                                gridArea='color'
                                size='S'
                                color={!isEmpty(labelColorMapSnapshot) ? labelColorMapSnapshot[name] : undefined}
                                onColorChange={onColorChange(name)}
                            />
                        ) : (
                            <LabelGroup />
                        )}
                        {name}
                    </Flex>
                </Flex>
            </View>

            <Divider size='M' />

            {!isEmpty(children) && (
                <ul
                    role='group'
                    key={`treeitem-group-${uid}`}
                    id={`treeitem-group-${uid}`}
                    data-testid={`treeitem-group-${uid}`}
                    className={classes.treeGroup}
                    hidden={isHidden}
                >
                    {children.map((objChild: Record<string, unknown>, idx: number) => (
                        <BuildTree
                            obj={objChild}
                            disabled={disabled}
                            key={idx}
                            isLabelSelected={isLabelSelected}
                            labelsInitiallyCollapsed={labelsInitiallyCollapsed}
                            onColorChange={onColorChange}
                            labelColorMapSnapshot={labelColorMapSnapshot}
                            isLabelIndeterminate={isLabelIndeterminate}
                            onToggleLabelSelection={onToggleLabelSelection}
                        />
                    ))}
                </ul>
            )}
        </li>
    );
};

export const DatasetImportToNewProjectLabels = ({
    datasetImportItem,
    patchDatasetImport,
    labelsInitiallyCollapsed = false,
}: DatasetImportToNewProjectLabelsProps): JSX.Element => {
    const { id, labels, labelsToSelect, firstChainLabels, labelColorMap, taskType } = datasetImportItem;

    const [labelColorMapSnapshot, setLabelColorMapSnapshot] = useState<Record<string, string>>(labelColorMap);

    const { paths, firstChainPaths } = getPaths(taskType, firstChainLabels, labelsToSelect);

    const findParents = useCallback(
        (label: DatasetImportLabel, initialArray: DatasetImportLabel[]): DatasetImportLabel[] => {
            if (isEmpty(label.parent)) return initialArray;

            const parentLabel = labelsToSelect.find(
                (labelItem: DatasetImportLabel) => labelItem.name === label.parent
            ) as DatasetImportLabel;

            return findParents(parentLabel, [...initialArray, parentLabel]);
        },
        [labelsToSelect]
    );

    const findChildren = (
        label: DatasetImportLabel,
        sourceArray: DatasetImportLabel[],
        initialArray: DatasetImportLabel[]
    ): DatasetImportLabel[] => {
        const levelChildren: DatasetImportLabel[] = sourceArray.filter(
            (labelItem: DatasetImportLabel): boolean => labelItem.parent === label.name
        );

        if (isEmpty(levelChildren)) return initialArray;

        const subLevelChildren: DatasetImportLabel[] = [];

        for (const labelItem of levelChildren) {
            subLevelChildren.push(...findChildren(labelItem, sourceArray, [...initialArray, labelItem]));
        }

        return subLevelChildren;
    };

    const selectAllLabels = useCallback(
        (state: boolean): void => {
            patchDatasetImport({ id, labels: state ? [...firstChainLabels, ...labelsToSelect] : firstChainLabels });
        },
        [firstChainLabels, id, labelsToSelect, patchDatasetImport]
    );

    const areAllLabelsSelected: boolean = useMemo((): boolean => {
        return labelsToSelect.every((labelToSelect: DatasetImportLabel) =>
            labels.find((label: DatasetImportLabel): boolean => label.name === labelToSelect.name)
        );
    }, [labels, labelsToSelect]);

    const areAllLabelsIndeterminate: boolean = useMemo((): boolean => {
        return (
            !areAllLabelsSelected &&
            labelsToSelect.some((labelToSelect: DatasetImportLabel) =>
                labels.find((label: DatasetImportLabel): boolean => label.name === labelToSelect.name)
            )
        );
    }, [areAllLabelsSelected, labels, labelsToSelect]);

    const isLabelSelected = useCallback(
        (labelName: string): boolean => {
            const isSelfSelected = !!labels.find((label: DatasetImportLabel): boolean => label.name === labelName);
            const labelChildren: DatasetImportLabel[] = labelsToSelect.filter(
                (label: DatasetImportLabel): boolean => label.parent === labelName
            );

            return !!labelChildren.length
                ? isSelfSelected || intersectionBy(labels, labelChildren, 'name').length === labelChildren.length
                : isSelfSelected;
        },
        [labels, labelsToSelect]
    );

    const isLabelIndeterminate = useCallback(
        (labelName: string): boolean => {
            const label: DatasetImportLabel = [...firstChainLabels, ...labelsToSelect].find(
                (labelToSelect: DatasetImportLabel): boolean => labelToSelect.name === labelName
            ) as DatasetImportLabel;

            const labelChildren: DatasetImportLabel[] = findChildren(label, labelsToSelect, []);
            const selectedChildren: DatasetImportLabel[] = findChildren(label, labels, []);

            return !!labelChildren.length
                ? !!selectedChildren.length
                    ? isLabelSelected(labelName) && selectedChildren.length !== labelChildren.length
                    : false
                : false;
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [isLabelSelected, labels, labelsToSelect]
    );

    const handleColorChangeEnd = (name: string) => (newColor: string) => {
        setLabelColorMapSnapshot((prevColors: Record<string, string>) => {
            const newColors = {
                ...prevColors,
                [name]: newColor,
            };

            patchDatasetImport({ id, labelColorMap: newColors });

            return newColors;
        });
    };

    const toggleLabelSelection = useCallback(
        (labelName: string): void => {
            let selectedLabels;

            const label = labelsToSelect.find(
                (labelsToSelectScopeLabel: DatasetImportLabel) => labelsToSelectScopeLabel.name === labelName
            ) as DatasetImportLabel;

            const isAlreadySelected = !!labels.find(
                (labelsScopeLabel: DatasetImportLabel) => labelsScopeLabel.name === label.name
            );

            if (isAlreadySelected) {
                selectedLabels = differenceBy(labels, [label, ...findChildren(label, labelsToSelect, [])], 'name');
            } else {
                selectedLabels = uniqBy(
                    [...labels, label, ...findParents(label, []), ...findChildren(label, labelsToSelect, [])],
                    'name'
                );
            }

            patchDatasetImport({ id, labels: selectedLabels });
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [findParents, id, labels, labelsToSelect, patchDatasetImport]
    );

    return (
        <div aria-label='dataset-import-to-new-project-labels' className={classes.labelsWrapper}>
            {isEmpty(labelsToSelect) ? (
                <IllustratedMessage>
                    <NotFound />
                    <Heading>No labels</Heading>
                </IllustratedMessage>
            ) : (
                <Flex direction='column' height='100%'>
                    <Flex alignItems='center' gap='size-200'>
                        <Checkbox
                            id='select-all-labels'
                            aria-label='select-all-labels'
                            onChange={selectAllLabels}
                            isSelected={areAllLabelsSelected}
                            isIndeterminate={areAllLabelsIndeterminate}
                            UNSAFE_style={{ paddingRight: 0 }}
                        />
                        <Text>Select all labels</Text>
                    </Flex>

                    {isTaskChainedProject(taskType) && (
                        <View
                            marginTop='size-150'
                            marginBottom='size-250'
                            UNSAFE_style={{ overflow: 'auto' }}
                            minHeight={'size-1250'}
                        >
                            <ul id='tree-root-first-task-group' data-testid='tree-root-first-task-group'>
                                {getLabelsStructureFromPaths(firstChainPaths).map(
                                    (obj: Record<string, unknown>, idx: number) => (
                                        <BuildTree
                                            obj={obj}
                                            disabled
                                            key={idx}
                                            isLabelSelected={isLabelSelected}
                                            labelsInitiallyCollapsed={labelsInitiallyCollapsed}
                                            onColorChange={handleColorChangeEnd}
                                            labelColorMapSnapshot={labelColorMapSnapshot}
                                            isLabelIndeterminate={isLabelIndeterminate}
                                            onToggleLabelSelection={toggleLabelSelection}
                                        />
                                    )
                                )}
                            </ul>
                        </View>
                    )}

                    <View marginTop='size-150' UNSAFE_style={{ overflow: 'auto' }}>
                        <ul id='tree-root-main-group' data-testid='tree-root-main-group'>
                            {getLabelsStructureFromPaths(paths).map((obj: Record<string, unknown>, idx: number) => (
                                <BuildTree
                                    obj={obj}
                                    key={idx}
                                    isLabelSelected={isLabelSelected}
                                    labelsInitiallyCollapsed={labelsInitiallyCollapsed}
                                    onColorChange={handleColorChangeEnd}
                                    labelColorMapSnapshot={labelColorMapSnapshot}
                                    isLabelIndeterminate={isLabelIndeterminate}
                                    onToggleLabelSelection={toggleLabelSelection}
                                />
                            ))}
                        </ul>
                    </View>
                </Flex>
            )}
        </div>
    );
};
