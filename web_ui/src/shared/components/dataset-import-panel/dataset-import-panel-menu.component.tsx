// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useCallback, useMemo } from 'react';

import { Item, Menu, MenuTrigger, Text } from '@adobe/react-spectrum';
import { ActionButton } from '@geti/ui';
import { OverlayTriggerState } from '@react-stately/overlays';
import { capitalize, difference, isEmpty } from 'lodash-es';

import { MoreMenu } from '../../../assets/icons';
import { DATASET_IMPORT_STATUSES } from '../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../core/datasets/dataset.interface';
import { matchStatus } from '../../../providers/dataset-import-to-existing-project-provider/utils';
import { useTusUpload } from '../../../providers/tus-upload-provider/tus-upload-provider.component';
import { isUploadingStatus } from './util';

enum MENU_ITEMS {
    IMPORT = 'import',
    CANCEL = 'cancel',
    DELETE = 'delete',
}

interface DatasetImportPanelMenuProps {
    isDisabled?: boolean;
    datasetImportItem: DatasetImportItem;
    primaryActionName?: string;
    datasetImportDeleteDialogTrigger: OverlayTriggerState;
    isReady: (id: string | undefined) => boolean;
    onDeleteAction: () => void;
    onPrimaryAction: () => void;
    setActiveDatasetImportId: (id: string | undefined) => void;
    abortDatasetImportAction: (uploadId: string | null) => void;
}

export const DatasetImportPanelMenu = ({
    isDisabled = false,
    primaryActionName,
    datasetImportItem,
    datasetImportDeleteDialogTrigger,
    isReady,
    onDeleteAction,
    onPrimaryAction,
    setActiveDatasetImportId,
    abortDatasetImportAction,
}: DatasetImportPanelMenuProps): JSX.Element => {
    const { abortActiveUpload } = useTusUpload();

    const disabledMenuItems = useMemo((): string[] => {
        const disabledItems = new Set<string>();

        if (isUploadingStatus(datasetImportItem)) {
            disabledItems.add(MENU_ITEMS.DELETE);
        }

        if (!isUploadingStatus(datasetImportItem)) {
            disabledItems.add(MENU_ITEMS.CANCEL);
        }

        if (
            !isReady(datasetImportItem.id) ||
            matchStatus(datasetImportItem, [
                DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
            ])
        ) {
            disabledItems.add(MENU_ITEMS.IMPORT);
        }

        return Array.from(disabledItems);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [datasetImportItem]);

    const menuItems = useMemo((): Record<string, string>[] => {
        const allItems = Object.values(MENU_ITEMS);

        return difference(allItems, disabledMenuItems).map((menuItem: string) => ({ name: menuItem }));
    }, [disabledMenuItems]);

    const getMenuItemName = useCallback(
        (item: Record<string, string>): JSX.Element => {
            switch (item.name) {
                case MENU_ITEMS.CANCEL:
                case MENU_ITEMS.DELETE:
                    return <Text>{capitalize(item.name)}</Text>;
                default:
                    return <Text>{capitalize(primaryActionName ?? item.name)}</Text>;
            }
        },
        [primaryActionName]
    );

    const handleMenuAction = (key: Key) => {
        switch (key) {
            case MENU_ITEMS.IMPORT:
                onPrimaryAction();
                break;
            case MENU_ITEMS.CANCEL:
                if (matchStatus(datasetImportItem, DATASET_IMPORT_STATUSES.UPLOADING)) {
                    abortActiveUpload(datasetImportItem.id);
                    onDeleteAction();
                } else {
                    abortDatasetImportAction(datasetImportItem.uploadId);
                }

                break;
            case MENU_ITEMS.DELETE:
                setActiveDatasetImportId(datasetImportItem.id);
                datasetImportDeleteDialogTrigger.open();
                break;
        }
    };

    return (
        <MenuTrigger>
            <ActionButton
                isQuiet
                isHidden={isEmpty(menuItems)}
                aria-label={'dataset-import-menu'}
                isDisabled={isDisabled}
            >
                <MoreMenu />
            </ActionButton>
            <Menu items={menuItems} disabledKeys={disabledMenuItems} onAction={(key: Key) => handleMenuAction(key)}>
                {(item) => (
                    <Item key={item.name} textValue={item.name} aria-label='dataset-import-menu-item'>
                        {getMenuItemName(item)}
                    </Item>
                )}
            </Menu>
        </MenuTrigger>
    );
};
