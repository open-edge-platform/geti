// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, View } from '@adobe/react-spectrum';
import { useNavigate } from 'react-router-dom';

import { ReactComponent as Logo } from '../../../assets/geti.svg';
import { paths } from '../../../core/services/routes';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { BackButton } from '../back-button/back-button.component';
import { HeaderActions } from './header-actions/header-actions.component';

import classes from './header.module.scss';

interface LandingPageHeaderProps {
    isProject: boolean;
    isDarkMode?: boolean;
    actionsEnabled?: boolean;
    withBackButton?: boolean;
    isAnomalyProject?: boolean;
}

const HeaderLogoLink = ({ withBackButton, isDarkMode }: { withBackButton: boolean; isDarkMode: boolean }) => {
    const navigate = useNavigate();
    const { workspaceId, organizationId } = useFirstWorkspaceIdentifier();

    const goBack = () => {
        navigate(paths.home({ organizationId, workspaceId }));
    };

    return (
        <div onClick={goBack} className={classes.headerLogoLink} aria-label='intel geti'>
            {withBackButton ? (
                <Flex marginStart={'size-300'} id={'application-logo'}>
                    <BackButton onPress={goBack} />
                </Flex>
            ) : (
                <View
                    marginStart={isDarkMode ? 'size-400' : 'size-200'}
                    height={'size-400'}
                    marginY={'auto'}
                    id={'application-logo'}
                >
                    <Logo />
                </View>
            )}
        </div>
    );
};

export const LandingPageHeader = ({
    isProject,
    isDarkMode = true,
    actionsEnabled = true,
    withBackButton = false,
    isAnomalyProject = false,
}: LandingPageHeaderProps): JSX.Element => {
    return (
        <>
            <Flex
                UNSAFE_className={isDarkMode ? classes.gray200color : classes.energyBlueShade1Color}
                justifyContent={'space-between'}
                height={'100%'}
                maxHeight={'size-800'}
                alignItems={'center'}
                data-testid={'application-header'}
            >
                <Flex height={'100%'}>
                    <View isHidden={isDarkMode} minWidth={'size-200'} UNSAFE_className={classes.energyBlueColor} />

                    <HeaderLogoLink isDarkMode={isDarkMode} withBackButton={withBackButton} />
                </Flex>

                {actionsEnabled && (
                    <HeaderActions isDarkMode={isDarkMode} isProject={isProject} isAnomalyProject={isAnomalyProject} />
                )}
            </Flex>
            <View
                isHidden={isDarkMode}
                height={'size-200'}
                width={'size-200'}
                UNSAFE_className={classes.energyBlueShade1Color}
                position={'absolute'}
            />
            <View
                isHidden={isDarkMode}
                height={'size-100'}
                width={'size-100'}
                UNSAFE_className={classes.energyBlueShade1Color}
                position={'absolute'}
                marginStart={'size-200'}
                marginTop={'size-200'}
            />
        </>
    );
};
