// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Flex, Radio, RadioGroup, Text } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import { useMediaQuery } from '@react-spectrum/utils';
import { View } from '@react-spectrum/view';
import isEqual from 'lodash/isEqual';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { Arrow } from '../../../../shared/components/arrow/arrow.component';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { Card } from '../card.component';
import { TaskChainMetadata, TaskChainTemplateProps } from './project-template.interface';

import taskChainClasses from './project-template.module.scss';

const joinDomains = (domains: DOMAIN[]) => domains.join('-');

export const TaskChainTemplate = ({
    setSelectedDomains,
    selectedDomains,
    subDomains,
}: TaskChainTemplateProps): JSX.Element => {
    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    useEffect(() => {
        if (selectedDomains.length < 2) {
            setSelectedDomains(subDomains[0].domains, subDomains[0].relations);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <RadioGroup
            aria-label='subdomains'
            value={joinDomains(selectedDomains)}
            onChange={(value) => {
                const domains = value.split('-') as DOMAIN[];
                const sub = subDomains.find((chain) => isEqual(chain.domains, domains));

                if (sub) {
                    setSelectedDomains(domains, sub.relations);
                }
            }}
        >
            <Flex
                gap={{ base: 'size-175', L: 'size-300' }}
                UNSAFE_className={taskChainClasses.projectCreationWellWrapper}
            >
                {subDomains.map((chain: TaskChainMetadata) => (
                    <Card
                        onPress={() => setSelectedDomains(chain.domains, chain.relations)}
                        id={`project-creation-${idMatchingFormat(joinDomains(chain.domains))}-chain`}
                        isSelected={isEqual(chain.domains, selectedDomains)}
                        isLargeSize={isLargeSize}
                        key={idMatchingFormat(joinDomains(chain.domains))}
                        description={chain.description}
                        titleComponent={
                            <View backgroundColor={'gray-200'} padding='size-200'>
                                <Flex direction='row' gap='size-175' alignItems={'center'}>
                                    <Radio value={joinDomains(chain.domains)} margin={0} />
                                    <Heading level={4} margin={0} data-testid={chain.domains.join('-')}>
                                        <Flex gap={'size-50'}>
                                            {chain.domains.map((domain, index) => (
                                                <Flex key={domain} gap={'size-50'}>
                                                    <Text>{domain}</Text>
                                                    <Arrow isHidden={index >= chain.domains.length - 1} />
                                                </Flex>
                                            ))}
                                        </Flex>
                                    </Heading>
                                </Flex>
                            </View>
                        }
                    />
                ))}
            </Flex>
        </RadioGroup>
    );
};
