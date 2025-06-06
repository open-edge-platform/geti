// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useMemo, useState } from 'react';

import { ActionButton, Checkbox, Divider, Flex, Heading, IllustratedMessage, Text, View } from '@geti/ui';
import { ChevronRightSmallLight, LabelGroup, NotFound } from '@geti/ui/icons';
import { differenceBy, intersectionBy, isEmpty, uniqBy } from 'lodash-es';

import { DATASET_IMPORT_TASK_TYPE } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportLabel, DatasetImportToNewProjectItem } from '../../../../../core/datasets/dataset.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { ColorPickerDialog } from '../../../../create-project/components/project-labels-management/task-labels-management/color-picker-dialog.component';
import { getLabelFullPath, getLabelsStructureFromPaths, isTaskChainedProject } from './utils';

import classes from './dataset-import-to-new-project.module.scss';

interface BuildTreeProps {
    obj: Record<string, unknown>;
    disabled?: boolean;
    hasCheckbox: boolean;
    labelsInitiallyCollapsed?: boolean;
    isLabelSelected: (labelName: string) => boolean;
    isLabelIndeterminate: (labelName: string) => boolean;
    onToggleLabelSelection: (labelName: string) => void;
    labelColorMapSnapshot: Record<string, string>;
    onColorChange: (name: string) => (newColor: string) => void;
}

interface DatasetImportToNewProjectLabelsProps {
    hasCheckbox: boolean;
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
    hasCheckbox,
    labelsInitiallyCollapsed,
    labelColorMapSnapshot,
    isLabelSelected,
    isLabelIndeterminate,
    onColorChange,
    onToggleLabelSelection,
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
                    {!!obj.label && hasCheckbox && (
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
                            hasCheckbox={hasCheckbox}
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
    hasCheckbox,
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
                    {hasCheckbox && (
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
                    )}

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
                                            hasCheckbox={hasCheckbox}
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
                                    hasCheckbox={hasCheckbox}
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
