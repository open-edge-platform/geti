// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedMediaImage } from 'mocks/mock-media';
import { render } from 'test-utils/render';

import { AnnotateButton } from './annotate-button.component.tauri';

const isAssistantAvailable = vi.fn(() => true);

vi.mock('@geti-ui/ui/icons', () => ({
    ChevronDownSmall: () => null,
    AcceptCircle: () => null,
    CrossCircle: () => null,
    Alert: () => null,
    Info: () => null,
    CloseSmall: () => null,
}));
vi.mock('../../media-preview/utils', () => ({ useAnnotatorMode: () => ['annotation', vi.fn()] }));

vi.mock('../../../ai-assistant/platform', () => ({
    isAssistantAvailable: () => isAssistantAvailable(),
}));

vi.mock('../../../ai-assistant/components/assistant-drawer.component', () => ({
    AssistantDrawer: ({ onClose }: { onClose: () => void }) => (
        <div>
            <span>ChatGPT assistant</span>
            <button onClick={onClose}>Close assistant</button>
        </div>
    ),
}));

vi.mock('hooks/use-project-identifier.hook', () => ({
    useProjectIdentifier: () => 'project-123',
}));

describe('AnnotateButton (desktop)', () => {
    const items = [getMockedMediaImage({ id: 'image-1' })] as Media[];

    it('opens project chat from the split button menu', async () => {
        const onClick = vi.fn();

        render(<AnnotateButton items={items} onClick={onClick} />);

        await userEvent.click(screen.getByRole('button', { name: 'More annotate options' }));
        await userEvent.click(await screen.findByRole('menuitem', { name: 'Ask ChatGPT about this project' }));

        expect(await screen.findByText('ChatGPT assistant')).toBeVisible();
        expect(onClick).not.toHaveBeenCalled();
    });

    it('still annotates when the primary action is used', async () => {
        const onClick = vi.fn();

        render(<AnnotateButton items={items} onClick={onClick} />);

        await userEvent.click(screen.getByRole('button', { name: 'Annotate' }));

        await waitFor(() => expect(onClick).toHaveBeenCalled());
        expect(screen.queryByText('ChatGPT assistant')).not.toBeInTheDocument();
    });

    it('hides the menu on operating systems without the assistant', async () => {
        isAssistantAvailable.mockReturnValueOnce(false);

        render(<AnnotateButton items={items} />);

        expect(screen.getByRole('button', { name: 'Annotate' })).toBeVisible();
        expect(screen.queryByRole('button', { name: 'More annotate options' })).not.toBeInTheDocument();
    });
});
