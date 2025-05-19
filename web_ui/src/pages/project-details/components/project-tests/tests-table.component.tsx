// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useMemo, useState } from 'react';

import {
    Cell,
    Column,
    Content,
    Flex,
    Heading,
    IllustratedMessage,
    Row,
    Link as SpectrumLink,
    TableBody,
    TableHeader,
    TableView,
    Text,
    useCollator,
} from '@geti/ui';
import { SortDescriptor } from '@react-types/shared';
import { capitalize, isEmpty } from 'lodash-es';
import { Link } from 'react-router-dom';

import { NoTests as NoTestsImage } from '../../../../assets/images';
import { isAnomalyDomain, isDetectionDomain, isSegmentationDomain } from '../../../../core/projects/domains';
import { paths } from '../../../../core/services/routes';
import { JobInfoStatus } from '../../../../core/tests/dtos/tests.interface';
import { useTests } from '../../../../core/tests/hooks/use-tests.hook';
import { isTestJobCompleted } from '../../../../core/tests/utils';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { ThreeDotsFlashing } from '../../../../shared/components/three-dots-flashing/three-dots-flashing.component';
import { TruncatedTextWithTooltip } from '../../../../shared/components/truncated-text/truncated-text.component';
import { SpectrumTableLoadingState } from '../../../../shared/utils';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { AccuracyTestCell } from './accuracy-test-cell.component';
import { TestItemSubmenu } from './test-item-submenu.component';
import { TestsTableKeys, TestsTableProps } from './tests-list.interface';
import { COLUMNS, formatTestDate, formatTestTime, getTestsTableData } from './utils';

import classes from './tests.module.scss';

const ShowDotsFlashing = ({ isFlashing, children }: { isFlashing: boolean; children: ReactNode }) => {
    return isFlashing ? (
        <Flex justifyContent={'center'} alignItems={'center'}>
            <ThreeDotsFlashing />
        </Flex>
    ) : (
        <>{children}</>
    );
};

export const NoTests = (): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();

    return (
        <IllustratedMessage>
            <NoTestsImage />
            <Heading>No tests</Heading>
            <Content>
                <Text>
                    Run a test to evaluate one of your trained models on a dedicated test set. To receive a live
                    prediction with your active model on a single image, you can use{' '}
                    <SpectrumLink>
                        <Link to={paths.project.tests.livePrediction(projectIdentifier)} viewTransition>
                            live prediction
                        </Link>
                    </SpectrumLink>
                </Text>
            </Content>
        </IllustratedMessage>
    );
};

export const TestsTable = ({ tests, isLoading }: TestsTableProps): JSX.Element => {
    const collator = useCollator({});
    const { useDeleteTestMutation } = useTests();
    const { isSingleDomainProject, isTaskChainProject } = useProject();
    const deleteTest = useDeleteTestMutation();
    const { projectId, workspaceId, organizationId } = useProjectIdentifier();
    const [disabledRowKeys, setDisabledRowKeys] = useState(['']);
    const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>();

    const handleDeleteTest = (testId: string) => {
        setDisabledRowKeys([...disabledRowKeys, testId]);

        deleteTest.mutate(
            { projectIdentifier: { organizationId, workspaceId, projectId }, testId },
            {
                onSuccess: () => {
                    // Remove the deleted testId from the list of disabled rows
                    const filteredRowKeys = disabledRowKeys.filter((key) => key !== testId);

                    setDisabledRowKeys(filteredRowKeys);
                },
            }
        );
    };

    const shouldShowGlobalLocalScore =
        isSingleDomainProject(isAnomalyDomain) &&
        (isSingleDomainProject(isDetectionDomain) || isSingleDomainProject(isSegmentationDomain));

    const testsItems = useMemo(() => {
        const items = getTestsTableData(tests);

        if (sortDescriptor === undefined) {
            return items;
        }

        return items.sort((a, b) => {
            /* @ts-expect-error Column from sort descriptor is used to get value from the current row */
            const rowA = sortDescriptor.column ? a[sortDescriptor.column] : '';
            /* @ts-expect-error Column from sort descriptor is used to get value from the current row */
            const rowB = sortDescriptor.column ? b[sortDescriptor.column] : '';

            const cmp = collator.compare(rowA, rowB);

            return sortDescriptor.direction === 'descending' ? cmp * -1 : cmp;
        });
    }, [tests, sortDescriptor, collator]);

    if (isEmpty(testsItems)) {
        return <NoTests />;
    }

    return (
        <Flex direction={'column'} flex={1}>
            <TableView
                aria-label={'Table with testing sets'}
                id={'tests-table-id'}
                sortDescriptor={sortDescriptor}
                onSortChange={setSortDescriptor}
                density={'spacious'}
                minHeight={isEmpty(testsItems) ? 600 : undefined}
                overflowMode={'truncate'}
                disabledKeys={disabledRowKeys}
                UNSAFE_className={classes.table}
            >
                <TableHeader
                    columns={COLUMNS.filter((column) =>
                        isTaskChainProject ? true : column.key !== 'taskType' ? true : false
                    )}
                >
                    {({ name, key, width }) => (
                        <Column
                            key={key}
                            align='center'
                            hideHeader={name === 'Submenu'}
                            allowsSorting={name !== 'Submenu'}
                            maxWidth={width ?? undefined}
                        >
                            <Text>{name}</Text>
                        </Column>
                    )}
                </TableHeader>
                <TableBody items={testsItems} loadingState={isLoading ? SpectrumTableLoadingState.loading : undefined}>
                    {(item) => (
                        <Row
                            key={item.id}
                            href={
                                isTestJobCompleted(item.jobStatus)
                                    ? paths.project.tests.test({
                                          organizationId,
                                          workspaceId,
                                          projectId,
                                          testId: `${item.id}`,
                                      })
                                    : undefined
                            }
                            routerOptions={{ viewTransition: true }}
                        >
                            {(columnKey) => (
                                <Cell key={`${item.id}-${columnKey}-${item.jobStatus}`}>
                                    {columnKey == 'testName' ? (
                                        <>{item.testName}</>
                                    ) : columnKey === 'taskType' ? (
                                        <TruncatedTextWithTooltip
                                            id={`row-${item.datasetId}-${item.id}-${columnKey}-id`}
                                        >
                                            {capitalize(item.taskType.toLocaleString())}
                                        </TruncatedTextWithTooltip>
                                    ) : columnKey === 'scoreValue' ? (
                                        <ShowDotsFlashing isFlashing={item.jobStatus != JobInfoStatus.DONE}>
                                            <AccuracyTestCell
                                                id={`${item.datasetId}-${item.id}`}
                                                score={Number(item.scoreValue)}
                                                testName={String(item.testName)}
                                                scoreDescription={String(item.scoreDescription)}
                                                shouldShowGlobalLocalScore={shouldShowGlobalLocalScore}
                                            />
                                        </ShowDotsFlashing>
                                    ) : columnKey === 'modelTemplateName' ? (
                                        <Flex
                                            justifyContent={'center'}
                                            direction={'column'}
                                            id={`row-${item.datasetId}-${item.id}-${columnKey}-id`}
                                        >
                                            <TruncatedTextWithTooltip
                                                id={`row-${item.datasetId}-${item.id}-${columnKey}-names-id-
                                                group-${item.groupId}-model-${item.modelId}`}
                                            >
                                                {`${item.modelTemplateName} (${item.groupName})`}
                                            </TruncatedTextWithTooltip>

                                            <Text
                                                // eslint-disable-next-line max-len
                                                id={`row-${item.datasetId}-${item.id}-${columnKey}-version-${item.version}-id`}
                                                UNSAFE_className={classes.subtextCell}
                                            >
                                                {`Version ${item.version}`}
                                            </Text>
                                        </Flex>
                                    ) : columnKey === 'creationTime' ? (
                                        <Flex justifyContent={'center'} direction={'column'}>
                                            <Text id={`row-${item.datasetId}-${item.id}-${columnKey}-date-id`}>
                                                {formatTestDate(String(item.creationTime))}
                                            </Text>
                                            <Text
                                                id={`row-${item.datasetId}-${item.id}-${columnKey}-time-id`}
                                                UNSAFE_className={classes.subtextCell}
                                            >
                                                {formatTestTime(String(item.creationTime))}
                                            </Text>
                                        </Flex>
                                    ) : columnKey === 'submenu' ? (
                                        <TestItemSubmenu
                                            id={`${item.datasetId}-${item.id}`}
                                            testName={String(item.testName)}
                                            handleDeleteTest={() => handleDeleteTest(String(item.id))}
                                        />
                                    ) : ['numberOfImages', 'numberOfFrames', 'numberOfLabels', 'precision'].includes(
                                          String(columnKey)
                                      ) ? (
                                        <Flex
                                            id={`row-${item.datasetId}-${item.id}-${columnKey}-${idMatchingFormat(
                                                item[columnKey as TestsTableKeys]
                                            )}-id`}
                                            justifyContent={'center'}
                                        >
                                            <span title={String(item[columnKey as TestsTableKeys])}>
                                                {String(item[columnKey as TestsTableKeys])}
                                            </span>
                                        </Flex>
                                    ) : (
                                        <Text
                                            id={`row-${item.datasetId}-${item.id}-${columnKey}-${idMatchingFormat(
                                                item[columnKey as TestsTableKeys]
                                            )}-id`}
                                        >
                                            <span title={String(item[columnKey as TestsTableKeys])}>
                                                {String(item[columnKey as TestsTableKeys])}
                                            </span>
                                        </Text>
                                    )}
                                </Cell>
                            )}
                        </Row>
                    )}
                </TableBody>
            </TableView>
        </Flex>
    );
};
