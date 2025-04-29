// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Heading, Text, View } from '@adobe/react-spectrum';

import { CreateWorkspaceDialog } from './create-workspace-dialog.component';

export const CreateWorkspace = (): JSX.Element => {
    return (
        <View>
            <Heading level={6} margin={0}>
                New workspace
            </Heading>
            <Text>Bring your ideas, projects, and teams together in one place.</Text>
            <CreateWorkspaceDialog />
        </View>
    );
};
