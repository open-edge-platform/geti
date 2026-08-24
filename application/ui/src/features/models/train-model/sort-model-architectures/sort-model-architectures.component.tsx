// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Item, Picker, Section, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { SortingOptions } from './utils';

import styles from './sort-model-architectures.module.scss';

type SortItemType = {
    key: string;
    nameKey: string;
};

type SortWidgetProps = {
    sortBy: SortingOptions;
    onSort: (option: SortingOptions) => void;
    items: SortItemType[][];
    ariaLabel?: string;
};

type SortItemProps = {
    item: {
        key: string;
        nameKey: string;
    };
};

const SortModelArchitectureItem = ({ item }: SortItemProps) => {
    const { t } = useTranslation();

    return <Text>{t(item.nameKey)}</Text>;
};

export const SortModelArchitectures = ({ sortBy, onSort, items, ariaLabel }: SortWidgetProps) => {
    const { t } = useTranslation();
    return (
        <Picker
            isQuiet
            items={items}
            selectedKey={sortBy}
            onSelectionChange={(key) => onSort(key as SortingOptions)}
            aria-label={ariaLabel}
            UNSAFE_className={styles.sortModelArchitectures}
            labelAlign={'start'}
            labelPosition={'side'}
            label={t('models.sortModelsByLabel')}
            menuWidth={'size-3000'}
        >
            {(item) => {
                return (
                    <Section key={`${item[0].key}-${item[1].key}`}>
                        {item.map((option) => (
                            <Item key={option.key} textValue={t(option.nameKey)}>
                                <SortModelArchitectureItem item={option} />
                            </Item>
                        ))}
                    </Section>
                );
            }}
        </Picker>
    );
};
