// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Flex, Item, Picker, Text } from '@geti-ui/ui';
import { useQuery } from '@tanstack/react-query';

import { setAiConnection, useAiConnection } from '../connection';
import type { ConnectionStatus } from '../hooks/use-connection-status';
import { codexModels } from '../transport/codex-transport';

const ACCOUNT_DEFAULT = '__account_default__';

export const ChatGptModelPicker = ({ status, isBusy }: { status: ConnectionStatus; isBusy: boolean }) => {
    const { model, executable } = useAiConnection();
    const query = useQuery({
        queryKey: ['assistant', 'codex-models', executable, status.account?.email, status.account?.plan],
        queryFn: codexModels,
        enabled: status.account !== null,
        staleTime: 5 * 60 * 1000,
        retry: false,
        refetchOnWindowFocus: false,
    });
    const models = query.data ?? [];
    const options = [{ id: ACCOUNT_DEFAULT, label: 'Account default' }, ...models];
    // Preserve an explicit saved choice even if the list is temporarily unavailable.
    if (model && !models.some(({ id }) => id === model))
        options.push({ id: model, label: `${model} (saved selection)` });
    return (
        <Flex direction={'column'} gap={'size-75'}>
            <Picker
                width={'100%'}
                label={'Model'}
                items={options}
                selectedKey={model || ACCOUNT_DEFAULT}
                isDisabled={!status.isReady || isBusy}
                isLoading={query.isFetching}
                onSelectionChange={(key) => {
                    if (key !== null) setAiConnection({ model: key === ACCOUNT_DEFAULT ? '' : String(key) });
                }}
            >
                {(option) => <Item key={option.id}>{option.label}</Item>}
            </Picker>
            {query.isFetching && <Text>Loading available models…</Text>}
            {!query.isFetching && status.account !== null && (query.isError || models.length === 0) && (
                <Flex direction={'column'} gap={'size-75'}>
                    <div role={'status'}>
                        {query.isError
                            ? `Could not load models: ${query.error.message}`
                            : 'The account returned no models. You can use Account default or try again.'}
                    </div>
                    <Button
                        variant={'secondary'}
                        isDisabled={isBusy}
                        onPress={() => {
                            void query.refetch();
                        }}
                    >
                        Retry model list
                    </Button>
                </Flex>
            )}
        </Flex>
    );
};
