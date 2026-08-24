// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Form,
    Heading,
    Item,
    Picker,
    Text,
} from '@geti-ui/ui';
import { Info } from '@geti-ui/ui/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty } from 'lodash-es';

import { getQueryKey } from '../../../../../../query-client/query-client';
import { useAssignMediaToExistingDatasetView } from '../api/use-assign-media-to-existing-dataset-view';
import { SelectedMediaCount } from '../selected-media-count/selected-media-count.component';
import { DatasetView } from '../type';

import classes from './assign-to-existing-view.module.scss';

const useAssignMediaToExistingView = () => {
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();

    const assignToExistingViewMutation = useAssignMediaToExistingDatasetView();

    const assignToExistingView = (selectedDatasetViewId: string, selectedMediaIds: string[], onClose: () => void) => {
        assignToExistingViewMutation.mutate(
            {
                params: {
                    path: {
                        project_id: projectId,
                        dataset_view_id: selectedDatasetViewId,
                    },
                },
                body: {
                    media_ids: selectedMediaIds,
                },
            },
            {
                onSuccess: async () => {
                    await Promise.all([
                        queryClient.invalidateQueries({
                            queryKey: getQueryKey([
                                'get',
                                '/api/projects/{project_id}/dataset/views/{dataset_view_id}/media',
                                {
                                    params: {
                                        path: {
                                            project_id: projectId,
                                            dataset_view_id: selectedDatasetViewId,
                                        },
                                    },
                                },
                            ]),
                        }),
                        // TODO: double-check if we can avoid invalidating these two queries.
                        queryClient.invalidateQueries({
                            queryKey: getQueryKey([
                                'get',
                                '/api/projects/{project_id}/dataset/media',
                                {
                                    params: {
                                        path: {
                                            project_id: projectId,
                                        },
                                    },
                                },
                            ]),
                        }),
                        queryClient.invalidateQueries({
                            queryKey: getQueryKey([
                                'get',
                                '/api/projects/{project_id}/dataset/items',
                                {
                                    params: {
                                        path: {
                                            project_id: projectId,
                                        },
                                    },
                                },
                            ]),
                        }),
                    ]);

                    onClose();
                },
            }
        );
    };

    return {
        assignToExistingView,
        isPending: assignToExistingViewMutation.isPending,
    };
};

type AssignToExistingViewDialogProps = {
    datasetViews: DatasetView[];
    onClose: () => void;
    selectedMediaIds: string[];
};

const AssignToExistingViewDialog = ({ datasetViews, selectedMediaIds, onClose }: AssignToExistingViewDialogProps) => {
    const [selectedDatasetViewId, setSelectedDatasetViewId] = useState<string | null>(null);
    const { assignToExistingView, isPending } = useAssignMediaToExistingView();

    const assignMedia = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (selectedDatasetViewId === null) {
            return;
        }

        assignToExistingView(selectedDatasetViewId, selectedMediaIds, onClose);
    };

    return (
        <Dialog>
            <Heading>Assign to existing view</Heading>
            <Divider size={'S'} />
            <Content>
                <SelectedMediaCount count={selectedMediaIds.length} />
                <Form id={'assign-to-existing-view-form'} onSubmit={assignMedia} marginTop={'size-200'}>
                    <Picker
                        items={datasetViews}
                        label={'Assign to'}
                        placeholder={'Select a view'}
                        selectedKey={selectedDatasetViewId}
                        onSelectionChange={(viewId) => setSelectedDatasetViewId(viewId?.toString() ?? null)}
                    >
                        {(item) => <Item key={item.id}>{item.name}</Item>}
                    </Picker>
                </Form>
                <Flex gap={'size-50'} marginTop={'size-250'}>
                    <Info />
                    <Text UNSAFE_className={classes.note}>
                        This operation will not affect other media that were already assigned to this view.
                    </Text>
                </Flex>
            </Content>
            <ButtonGroup>
                <Button onPress={onClose} variant={'secondary'}>
                    Close
                </Button>
                <Button type={'submit'} form={'assign-to-existing-view-form'} variant={'accent'} isPending={isPending}>
                    Assign
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

type AssignToExistingViewProps = {
    datasetViews: DatasetView[];
    selectedMediaIds: string[];
};

export const AssignToExistingView = ({ datasetViews, selectedMediaIds }: AssignToExistingViewProps) => {
    const [isAssignToExistingViewOpen, setIsAssignToExistingViewOpen] = useState<boolean>(false);
    const isAssignToExistingViewDisabled = isEmpty(datasetViews);

    const closeDialog = () => {
        setIsAssignToExistingViewOpen(false);
    };

    return (
        <>
            <Button
                variant={'primary'}
                onPress={() => setIsAssignToExistingViewOpen(true)}
                isDisabled={isAssignToExistingViewDisabled}
            >
                Assign to existing view
            </Button>
            <DialogContainer onDismiss={closeDialog}>
                {isAssignToExistingViewOpen && (
                    <AssignToExistingViewDialog
                        datasetViews={datasetViews}
                        onClose={closeDialog}
                        selectedMediaIds={selectedMediaIds}
                    />
                )}
            </DialogContainer>
        </>
    );
};
