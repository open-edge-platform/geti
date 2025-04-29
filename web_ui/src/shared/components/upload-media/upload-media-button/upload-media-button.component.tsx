// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, Key, useRef } from 'react';

import { isFirefox } from '@react-aria/utils';
import isFunction from 'lodash/isFunction';

import { Share } from '../../../../assets/icons';
import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../../core/status/hooks/utils';
import { UPLOAD_MEDIA_LABEL } from '../../../../pages/project-details/components/project-media/utils';
import { mediaExtensionHandler } from '../../../../providers/media-upload-provider/media-upload.validator';
import { CANT_UPLOAD_FOLDER_FIREFOX } from '../../../custom-notification-messages';
import { VALID_MEDIA_TYPES_DISPLAY } from '../../../media-utils';
import { Button } from '../../button/button.component';
import { MenuTriggerButton } from '../../menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { useOnFileInputChange } from '../useFileInputChange.hook';
import { onMenuAction } from '../utils';
import { MenuItemsKey } from './upload-media-button.interface';

interface UploadMediaButtonProps {
    id: string;
    title: string;
    isQuiet?: boolean;
    acceptedFormats?: string[];
    ariaLabel?: string;
    variant?: ComponentProps<typeof Button>['variant'];
    multiple?: boolean;
    customClasses?: string;
    isDisabled?: boolean;
    uploadCallback: (files: File[]) => void;
    onCameraSelected: () => void;
}

export const UploadMediaButton = ({
    id,
    title,
    ariaLabel,
    variant = 'secondary',
    customClasses,
    acceptedFormats,
    isQuiet = false,
    multiple = true,
    isDisabled = false,
    uploadCallback,
    onCameraSelected,
}: UploadMediaButtonProps): JSX.Element => {
    const { data: status } = useStatus();
    const fileInputRef = useRef<HTMLInputElement>({} as HTMLInputElement);

    const isUploadMediaDisabled = isBelowTooLowFreeDiskSpace(status?.freeSpace ?? 0);
    const { onFileInputChange } = useOnFileInputChange({ uploadCallback });

    // Disabled folder option if the user is using Firefox
    const isFolderOptionDisabled = isFirefox();

    const onMenuActionHandler = (key: Key) => {
        if (key === MenuItemsKey.CAMERA.toLowerCase()) {
            isFunction(onCameraSelected) && onCameraSelected();

            return;
        }

        onMenuAction(key, fileInputRef);
    };

    const menuItems = multiple
        ? [MenuItemsKey.FILES, MenuItemsKey.FOLDER, MenuItemsKey.CAMERA]
        : [MenuItemsKey.FILE, MenuItemsKey.CAMERA];

    return (
        <>
            <input
                hidden
                multiple={multiple}
                type='file'
                ref={fileInputRef}
                id={`${id}-input-file`}
                onChange={onFileInputChange}
                aria-label={ariaLabel ?? 'upload-media-input'}
                style={{ pointerEvents: 'all' }}
                onClick={() => (fileInputRef.current.value = '')}
                accept={mediaExtensionHandler(acceptedFormats ?? VALID_MEDIA_TYPES_DISPLAY)}
                disabled={isDisabled || isUploadMediaDisabled}
            />
            <MenuTriggerButton
                id={id}
                title={title}
                isQuiet={isQuiet}
                variant={variant}
                onAction={onMenuActionHandler}
                ariaLabel={ariaLabel ?? UPLOAD_MEDIA_LABEL}
                isDisabled={isDisabled || isUploadMediaDisabled}
                menuTooltip={CANT_UPLOAD_FOLDER_FIREFOX}
                icon={isQuiet ? <Share /> : undefined}
                items={menuItems}
                menuTriggerClasses={customClasses}
                disabledKeys={isFolderOptionDisabled ? [MenuItemsKey.FOLDER.toLocaleLowerCase()] : undefined}
                tooltipPlacement={'top'}
            />
        </>
    );
};
