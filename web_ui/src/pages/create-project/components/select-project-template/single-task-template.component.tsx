// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { Grid, minmax, repeat } from '@geti/ui';
import { useMediaQuery } from '@react-spectrum/utils';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { SUBDOMAIN } from '../../../../core/projects/project.interface';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { Card } from '../card.component';
import { DomainCardsMetadata, SingleTemplateProps } from './project-template.interface';

import classes from './project-template.module.scss';

export const SingleTaskTemplate = ({ cards, metaData, setSelectedDomains }: SingleTemplateProps): JSX.Element => {
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const [selectedSubDomain, setSelectedSubDomain] = useState<SUBDOMAIN>(cards[0].subDomain);
    const { FEATURE_FLAG_ANOMALY_REDUCTION } = useFeatureFlags();

    useEffect(() => {
        const [firstCard] = cards;
        const selectedCard =
            cards.find(({ domain, relation }) => domain === metaData?.domain && relation === metaData?.relation) ??
            firstCard;

        setSelectedDomains([selectedCard.domain], [selectedCard.relation]);
        setSelectedSubDomain(selectedCard.subDomain);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const gridColumns =
        cards.length === 1
            ? repeat('auto-fit', minmax('size-3000', 'size-4600'))
            : repeat('auto-fit', minmax('size-3000', '1fr'));

    return (
        <Grid
            id='domain-grid'
            gap={'size-150'}
            justifyItems={'center'}
            alignContent={'space-between'}
            columns={gridColumns}
            UNSAFE_className={classes.projectCreationWellWrapper}
            maxHeight={'size-3600'}
        >
            {cards.map(({ domain, disabled, id, subDomain, relation, ...rest }: DomainCardsMetadata) => {
                return (
                    <Card
                        {...rest}
                        id={id}
                        key={id}
                        title={
                            // Because of the literature (Anomaly Classification is named as Anomaly Detection) we do
                            // the mapping here
                            FEATURE_FLAG_ANOMALY_REDUCTION && subDomain === SUBDOMAIN.ANOMALY_CLASSIFICATION
                                ? SUBDOMAIN.ANOMALY_DETECTION
                                : subDomain
                        }
                        isLargeSize={isLargeSize}
                        onPress={() => {
                            !disabled && setSelectedDomains([domain], [relation]);
                            setSelectedSubDomain(subDomain);
                        }}
                        isSelected={selectedSubDomain === subDomain}
                        isDisabled={disabled}
                    />
                );
            })}
        </Grid>
    );
};
