// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { annotatorRender as render } from '../../../../annotator/test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../../annotator/zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../../annotator/zoom/zoom-provider.component';
import { Edge, EdgeProps } from './edge.component';

describe('Edge', () => {
    const renderApp = async ({
        id = 'edge-1',
        to = getMockedKeypointNode({ label: getMockedLabel({ color: 'green' }) }),
        from = getMockedKeypointNode({ label: getMockedLabel({ color: 'blue' }) }),
        isSelected = false,
        contextMenu = <></>,
        isDisabled = false,
        onSelect = jest.fn(),
        onNewIntermediatePoint = jest.fn(),
        onRemoveSelected = jest.fn(),
        onResetAndSelect = jest.fn(),
    }: Partial<EdgeProps>) => {
        await render(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <svg width='500' height='500'>
                        <Edge
                            id={id}
                            to={to}
                            from={from}
                            isSelected={isSelected}
                            contextMenu={contextMenu}
                            isDisabled={isDisabled}
                            onSelect={onSelect}
                            onNewIntermediatePoint={onNewIntermediatePoint}
                            onRemoveSelected={onRemoveSelected}
                            onResetAndSelect={onResetAndSelect}
                        />

                        <rect
                            x='467'
                            y='128'
                            width='16'
                            height='16'
                            fillOpacity='0'
                            fill='white'
                            aria-label='Resize keypoint'
                        ></rect>
                    </svg>
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    it('apply "selected" styles when an item is selected', async () => {
        const toLine = getMockedKeypointNode({ label: getMockedLabel({ color: 'green', name: '1' }) });
        const fromLine = getMockedKeypointNode({ label: getMockedLabel({ color: 'green', name: '2' }) });
        await renderApp({ isSelected: true, from: fromLine, to: toLine });

        const line1 = screen.getByLabelText('line - 1');
        expect(line1).toHaveClass('selected');
        expect(line1).toHaveStyle(`stroke: ${toLine.label.color}`);

        const line2 = screen.getByLabelText('line - 2');
        expect(line2).toHaveClass('selected');
        expect(line2).toHaveStyle(`stroke: ${fromLine.label.color}`);
    });

    describe('right-clicking hidden the line', () => {
        const getHiddenLine = (line1: string, line2: string) =>
            screen.getByLabelText(`hidden padded edge ${line1} - ${line2}`);

        const clickOutside = () => {
            fireEvent.mouseDown(document.body);
            fireEvent.mouseUp(document.body);
        };
        const toLine = getMockedKeypointNode({ label: getMockedLabel({ color: 'green', name: '1' }) });
        const fromLine = getMockedKeypointNode({ label: getMockedLabel({ color: 'green', name: '2' }) });

        it('open context menu and reset selection', async () => {
            const menuText = 'context menu';
            const mockedOnResetAndSelect = jest.fn();
            await renderApp({
                isSelected: true,
                contextMenu: <p>{menuText}</p>,
                onResetAndSelect: mockedOnResetAndSelect,
                to: toLine,
                from: fromLine,
            });

            fireEvent.contextMenu(getHiddenLine(fromLine.label.name, toLine.label.name));

            expect(screen.getByText(menuText)).toBeVisible();
            expect(mockedOnResetAndSelect).toHaveBeenCalled();
        });

        it('close the context menu when clicking outside', async () => {
            const menuText = 'context menu';
            const mockedOnRemoveSelected = jest.fn();
            await renderApp({
                isSelected: true,
                contextMenu: <p>{menuText}</p>,
                onRemoveSelected: mockedOnRemoveSelected,
                to: toLine,
                from: fromLine,
            });

            fireEvent.contextMenu(getHiddenLine(fromLine.label.name, toLine.label.name));
            expect(screen.getByText(menuText)).toBeVisible();

            clickOutside();

            await waitFor(() => {
                expect(screen.queryByText(menuText)).not.toBeInTheDocument();
                expect(mockedOnRemoveSelected).toHaveBeenCalled();
            });
        });

        it('clicking inside the menu elements does not close the context menu', async () => {
            const menuText = 'option 1';
            const mockedOnRemoveSelected = jest.fn();
            const mockedMenuOption = jest.fn();

            await renderApp({
                isSelected: true,
                contextMenu: <button onClick={mockedMenuOption}>{menuText}</button>,
                onRemoveSelected: mockedOnRemoveSelected,
                to: toLine,
                from: fromLine,
            });

            fireEvent.contextMenu(getHiddenLine(fromLine.label.name, toLine.label.name));
            fireEvent.click(screen.getByRole('button', { name: menuText }));

            expect(mockedMenuOption).toHaveBeenCalled();
            expect(screen.getByText(menuText)).toBeVisible();
        });

        it('clicking on a "resize keypoint" will not remove all selected elements but will close the menu', async () => {
            const menuText = 'context menu';
            const mockedOnRemoveSelected = jest.fn();
            await renderApp({
                isSelected: true,
                contextMenu: <p>{menuText}</p>,
                onRemoveSelected: mockedOnRemoveSelected,
                to: toLine,
                from: fromLine,
            });

            fireEvent.contextMenu(getHiddenLine(fromLine.label.name, toLine.label.name));
            expect(screen.getByText(menuText)).toBeVisible();

            const keypoint = screen.getByLabelText(/resize keypoint/i);
            fireEvent.mouseDown(keypoint);
            fireEvent.mouseUp(keypoint);

            await waitFor(() => {
                expect(screen.queryByText(menuText)).not.toBeInTheDocument();
                expect(mockedOnRemoveSelected).not.toHaveBeenCalled();
            });
        });
    });
});
