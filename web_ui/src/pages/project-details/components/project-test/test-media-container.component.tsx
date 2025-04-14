// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Grid, Item, Picker, repeat, Slider, View } from '@adobe/react-spectrum';
import uniqBy from 'lodash/uniqBy';
import { v4 as uuidv4 } from 'uuid';

import { Label } from '../../../../core/labels/label.interface';
import { filterOutExclusiveLabel, getNonEmptyLabelsFromProject } from '../../../../core/labels/utils';
import {
    AdvancedFilterOptions,
    SearchRuleField,
    SearchRuleOperator,
} from '../../../../core/media/media-filter.interface';
import { isClassificationDomain, isSegmentationDomain } from '../../../../core/projects/domains';
import { TASK_TYPE } from '../../../../core/projects/dtos/task.interface';
import { getDomain } from '../../../../core/projects/project.interface';
import { TestMediaItem } from '../../../../core/tests/test-media.interface';
import { Test } from '../../../../core/tests/tests.interface';
import { CardContent } from '../../../../shared/components/card-content/card-content.component';
import { SortDirection } from '../../../../shared/components/sort-by-attribute/sort-by-attribute.component';
import { hasEqualDomain, hasEqualId } from '../../../../shared/utils';
import { TaskProvider } from '../../../annotator/providers/task-provider/task-provider.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { MediaItemsBucket } from './media-items-bucket.component';
import { MediaItemsBucketTitle, MediaItemsBucketType } from './media-items-bucket.interface';
import { TestDetailsPreview } from './test-details-preview/test-details-preview.component';

interface LabelItems {
    id: string;
    name: string;
}

const DEFAULT_THRESHOLD = 0.5;

interface TestMediaContainerProps {
    taskType: TASK_TYPE;
    test: Test;
    modelInfo: string;
    selectedLabelId: string;
    onLabelChange: (label: LabelItems) => void;
}

const isSingleLabelSelection = (labels: Label[]) => {
    const userDefinedLabels = filterOutExclusiveLabel(labels);

    return uniqBy(userDefinedLabels, 'group').length === 1;
};

export const TestMediaContainer = ({
    taskType,
    test,
    modelInfo,
    selectedLabelId,
    onLabelChange,
}: TestMediaContainerProps): JSX.Element => {
    const {
        project: { tasks, domains },
        isTaskChainProject,
    } = useProject();
    const [threshold, setThreshold] = useState<number>(DEFAULT_THRESHOLD);

    const task = useMemo(() => {
        // Get the task used for this test based on the model info's task type
        const testDomain = getDomain(taskType.toLowerCase() as TASK_TYPE);

        return tasks.find(hasEqualDomain(testDomain));
    }, [taskType, tasks]);

    // TODO(@jpggvilaca): As a temporary workaround for issue with
    // 'No Object' images not shown in testing result for object detection:
    // hide all empty labels from the media container dropdown ("Empty", "No class", "No object").
    // This has been fixed for classification and detection, but not segmentation
    const labels = useMemo(() => {
        if (task === undefined || isSegmentationDomain(task.domain)) {
            return getNonEmptyLabelsFromProject(task ? [task] : tasks);
        }

        return task.labels;
    }, [task, tasks]);

    const isSingleClassificationDomainType = !isTaskChainProject && domains.some(isClassificationDomain);
    const hideModelAccuracySlider =
        !isTaskChainProject && domains.every(isClassificationDomain) && isSingleLabelSelection(labels);

    const formattedLabels = useMemo(() => {
        const mappedLabels: LabelItems[] = labels.map(({ id, name }) => ({ id, name }));

        // If we have more than 1 label, we want to add the option to filter by 'all labels'
        if (mappedLabels.length > 1) {
            mappedLabels.unshift({ id: 'null', name: 'All labels' });
        }

        return mappedLabels;
    }, [labels]);

    const [selectedTestItem, setSelectedTestItem] = useState<TestMediaItem | undefined>(undefined);
    const [selectedBucket, setSelectedBucket] = useState<{ type: MediaItemsBucketType; sortDir: SortDirection }>({
        type: MediaItemsBucketType.BELOW_THRESHOLD,
        sortDir: SortDirection.ASC,
    });

    const labelSearchRule = useMemo(
        () => ({
            value: selectedLabelId === 'null' ? null : selectedLabelId,
            field: SearchRuleField.LabelId,
            operator: SearchRuleOperator.Equal,
            id: uuidv4(),
        }),
        [selectedLabelId]
    );

    const mediaFilterOptionsBelowThresholdBucket: AdvancedFilterOptions = useMemo(
        () => ({
            condition: 'and',
            rules: [
                labelSearchRule,
                {
                    value: threshold,
                    field: SearchRuleField.Score,
                    operator: SearchRuleOperator.Less,
                    id: uuidv4(),
                },
            ],
        }),
        [threshold, labelSearchRule]
    );

    const mediaFilterOptionsAboveThresholdBucket: AdvancedFilterOptions = useMemo(
        () => ({
            condition: 'and',
            rules: [
                labelSearchRule,
                {
                    value: threshold,
                    field: SearchRuleField.Score,
                    operator: SearchRuleOperator.GreaterOrEqual,
                    id: uuidv4(),
                },
            ],
        }),
        [threshold, labelSearchRule]
    );

    const onBucketItemSelection = (item: TestMediaItem, bucketType: MediaItemsBucketType, sortDir: SortDirection) => {
        setSelectedTestItem(item);
        setSelectedBucket({ type: bucketType, sortDir });
    };

    return (
        <CardContent
            gridArea={'media'}
            title={'Annotations vs Predictions'}
            titleActions={
                <Picker
                    id={'select-label-id'}
                    aria-label={'Select label'}
                    items={formattedLabels}
                    selectedKey={selectedLabelId}
                    onSelectionChange={(key) =>
                        onLabelChange(formattedLabels.find(hasEqualId(String(key))) as LabelItems)
                    }
                >
                    {(item) => (
                        <Item aria-label={item.name} key={item.id} textValue={item.name}>
                            {item.name}
                        </Item>
                    )}
                </Picker>
            }
            actions={
                hideModelAccuracySlider ? undefined : (
                    <Slider
                        id={'score-threshold-id'}
                        label={'Model score threshold'}
                        formatOptions={{ style: 'percent' }}
                        labelPosition={'side'}
                        onChangeEnd={setThreshold}
                        minValue={0}
                        maxValue={1}
                        defaultValue={0.5}
                        step={0.01}
                        isFilled
                        width={'90%'}
                    />
                )
            }
        >
            <View paddingX={'size-700'} height={'100%'}>
                <Grid columns={repeat(2, '1fr')} columnGap={'size-900'} height={'100%'}>
                    <MediaItemsBucket
                        title={
                            isSingleClassificationDomainType
                                ? MediaItemsBucketTitle.INCORRECT
                                : MediaItemsBucketTitle.BELOW_THRESHOLD
                        }
                        selectedLabelId={selectedLabelId}
                        type={MediaItemsBucketType.BELOW_THRESHOLD}
                        mediaFilterOptions={mediaFilterOptionsBelowThresholdBucket}
                        setSelectedTestItem={(item, sortDir: SortDirection) =>
                            onBucketItemSelection(item, MediaItemsBucketType.BELOW_THRESHOLD, sortDir)
                        }
                        selectedMediaItem={selectedTestItem}
                    />
                    <MediaItemsBucket
                        title={
                            isSingleClassificationDomainType
                                ? MediaItemsBucketTitle.CORRECT
                                : MediaItemsBucketTitle.ABOVE_THRESHOLD
                        }
                        selectedLabelId={selectedLabelId}
                        type={MediaItemsBucketType.ABOVE_THRESHOLD}
                        mediaFilterOptions={mediaFilterOptionsAboveThresholdBucket}
                        setSelectedTestItem={(item, sortDir: SortDirection) =>
                            onBucketItemSelection(item, MediaItemsBucketType.ABOVE_THRESHOLD, sortDir)
                        }
                        selectedMediaItem={selectedTestItem}
                    />
                </Grid>
            </View>
            {selectedTestItem !== undefined && (
                <TaskProvider>
                    <TestDetailsPreview
                        test={test}
                        taskType={taskType}
                        selectedMediaItem={selectedTestItem}
                        setSelectedMediaItem={setSelectedTestItem}
                        modelInformation={modelInfo}
                        filter={
                            selectedBucket.type === MediaItemsBucketType.ABOVE_THRESHOLD
                                ? mediaFilterOptionsAboveThresholdBucket
                                : mediaFilterOptionsBelowThresholdBucket
                        }
                        sortDir={selectedBucket.sortDir}
                    />
                </TaskProvider>
            )}
        </CardContent>
    );
};
