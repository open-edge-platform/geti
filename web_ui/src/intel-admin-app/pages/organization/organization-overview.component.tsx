// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useEffect, useState } from 'react';

import { ActionGroup, ButtonGroup, Divider, Flex, Form, Item, Key, Text, TextField, View } from '@adobe/react-spectrum';
import CheckmarkCircleOutline from '@spectrum-icons/workflow/CheckmarkCircleOutline';
import DeleteOutline from '@spectrum-icons/workflow/DeleteOutline';
import RemoveCircle from '@spectrum-icons/workflow/RemoveCircle';
import dayjs from 'dayjs';
import isEmpty from 'lodash/isEmpty';
import { Navigate } from 'react-router-dom';
import { useOverlayTriggerState } from 'react-stately';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { AccountStatus, Organization } from '../../../core/organizations/organizations.interface';
import { paths } from '../../../core/services/routes';
import { Button } from '../../../shared/components/button/button.component';
import { DeleteDialog } from '../../../shared/components/delete-dialog/delete-dialog.component';
import { PhotoPlaceholder } from '../../../shared/components/photo-placeholder/photo-placeholder.component';
import { Header } from '../../shared/components/header/header.component';
import { useOrganization } from './hooks/organization.hook';

import classes from './organization.module.scss';

const ORGANIZATION_ACTIONS = {
    SUSPEND: 'suspend',
    ACTIVATE: 'activate',
    DELETE: 'delete',
};

export const OrganizationOverview = (): JSX.Element => {
    const { FEATURE_FLAG_CREDIT_SYSTEM, FEATURE_FLAG_REQ_ACCESS } = useFeatureFlags();
    const { organization, updateOrganization, isLoading } = useOrganization();

    const deleteTriggerState = useOverlayTriggerState({});

    const adminEmail = organization?.admins.length ? organization.admins[0].email : '';
    const adminFullName = organization?.admins.length
        ? [organization.admins[0].firstName, organization.admins[0].lastName].join(' ')
        : '';

    const [formState, setFormState] = useState<Pick<Organization, 'name'>>({
        name: organization?.name || '',
    });

    useEffect(() => {
        if (formState.name !== organization?.name) {
            setFormState({ name: organization?.name || '' });
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [organization]);

    const handleAction = (action: Key) => {
        if (action === ORGANIZATION_ACTIONS.SUSPEND && organization) {
            updateOrganization.mutate({ ...organization, status: AccountStatus.SUSPENDED });
        } else if (action === ORGANIZATION_ACTIONS.ACTIVATE && organization) {
            updateOrganization.mutate({ ...organization, status: AccountStatus.ACTIVATED });
        } else if (action === ORGANIZATION_ACTIONS.DELETE && organization) {
            deleteTriggerState.open();
        }
    };

    const handleOnSubmitOrganizationForm = (e: FormEvent) => {
        e.preventDefault();

        if (organization) {
            updateOrganization.mutate({ ...organization, ...formState });
        }
    };

    if (!FEATURE_FLAG_CREDIT_SYSTEM) {
        return <Navigate to={paths.intelAdmin.index({})} />;
    }

    return (
        <Flex direction={'column'} height={'100%'}>
            <Header title={'Overview'} />

            {organization && (
                <View flex={1} overflow={'hidden auto'}>
                    <View paddingX={'size-300'} UNSAFE_className={classes.organizationOverviewPicture}>
                        <PhotoPlaceholder
                            name={organization.name}
                            email={organization.name}
                            width={'size-1600'}
                            height={'size-1600'}
                        />
                    </View>
                    <ButtonGroup marginTop={'size-100'} isHidden>
                        <Button variant={'primary'} style={'fill'}>
                            Change
                        </Button>
                        <Button variant={'primary'} style={'fill'}>
                            Remove
                        </Button>
                    </ButtonGroup>
                    <Divider size={'S'} marginTop={'size-300'} />
                    <View paddingY={'size-300'}>
                        <Form onSubmit={handleOnSubmitOrganizationForm} isDisabled={isLoading}>
                            <Flex
                                direction={'column'}
                                gap={'size-300'}
                                alignContent={'start'}
                                maxWidth={{ M: 'size-4600', L: 'size-6000' }}
                            >
                                <TextField
                                    label={'Unique identifier'}
                                    value={organization.id}
                                    UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                                    data-testid={'organization-overview-id-input'}
                                    isReadOnly
                                />
                                <TextField
                                    label={'Email'}
                                    value={adminEmail}
                                    UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                                    data-testid={'organization-overview-email-input'}
                                    isReadOnly
                                />
                                <TextField
                                    label={'Name'}
                                    name={'name'}
                                    value={formState.name}
                                    UNSAFE_className={classes.textField}
                                    onChange={(value) => setFormState({ ...formState, name: value })}
                                    data-testid={'organization-overview-name-input'}
                                    isQuiet
                                />
                                <TextField
                                    label={'Admin'}
                                    value={adminFullName}
                                    UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                                    isReadOnly
                                />
                                <TextField
                                    label={'Status'}
                                    value={organization.status}
                                    UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                                    data-testid={'organization-overview-status-input'}
                                    isReadOnly
                                />
                                <TextField
                                    label={'Membership since'}
                                    value={dayjs(organization.createdAt).format('DD MMM YYYY, HH:mm A')}
                                    UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                                    data-testid={'organization-overview-created-at-input'}
                                    isReadOnly
                                />
                                <Button
                                    variant='accent'
                                    style='fill'
                                    type='submit'
                                    width={'size-900'}
                                    data-testid='organization-overview-save-button'
                                    isPending={isLoading}
                                >
                                    Save
                                </Button>
                            </Flex>
                        </Form>
                    </View>

                    <Divider size={'S'} marginTop={'size-300'} marginBottom={'size-300'} />

                    {FEATURE_FLAG_REQ_ACCESS && !isEmpty(organization.requestAccessReason) && (
                        <>
                            <TextField
                                label={'Use case of using Intel® Geti™'}
                                value={organization.requestAccessReason}
                                UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                                isReadOnly
                            />
                            <Divider size={'S'} marginTop={'size-300'} marginBottom={'size-300'} />{' '}
                        </>
                    )}

                    <ActionGroup
                        onAction={handleAction}
                        isDisabled={isLoading}
                        items={[
                            {
                                key: ORGANIZATION_ACTIONS.SUSPEND,
                                children: 'Suspend',
                                icon: <RemoveCircle size={'S'} />,
                            },
                            {
                                key: ORGANIZATION_ACTIONS.ACTIVATE,
                                children: 'Activate',
                                icon: <CheckmarkCircleOutline size={'S'} />,
                            },
                            {
                                key: ORGANIZATION_ACTIONS.DELETE,
                                children: 'Delete',
                                icon: <DeleteOutline size={'S'} />,
                            },
                        ].filter(
                            (item) =>
                                (item.key === ORGANIZATION_ACTIONS.SUSPEND &&
                                    organization?.status === AccountStatus.ACTIVATED) ||
                                (item.key === ORGANIZATION_ACTIONS.ACTIVATE &&
                                    organization?.status === AccountStatus.SUSPENDED) ||
                                (item.key === ORGANIZATION_ACTIONS.DELETE &&
                                    organization?.status !== AccountStatus.DELETED)
                        )}
                    >
                        {(item) => (
                            <Item key={item.key}>
                                {item.icon}
                                <Text>{item.children}</Text>
                            </Item>
                        )}
                    </ActionGroup>
                </View>
            )}
            <DeleteDialog
                title={'organization'}
                name={organization?.name || ''}
                onAction={() =>
                    organization && updateOrganization.mutate({ ...organization, status: AccountStatus.DELETED })
                }
                triggerState={deleteTriggerState}
            />
        </Flex>
    );
};
