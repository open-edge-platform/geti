// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { downloadFile } from '../../utils';
import { downloadMultiplePages, getContainerElements, getElementSize, getLegendsPositions } from './export-svg-utils';

jest.mock('../../utils', () => ({
    ...jest.requireActual('../../utils'),
    downloadFile: jest.fn(),
}));

const getMockedSvg = (width: number, height: number): SVGSVGElement => {
    return {
        clientWidth: width,
        clientHeight: height,
    } as SVGSVGElement;
};

describe('Download svg button utils', () => {
    const pageWidth = 400;
    const pageHeight = 400;
    const pagePadding = 20;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('downloadMultiplePages', () => {
        it('empty elements', async () => {
            const fileName = 'nameTest';
            await downloadMultiplePages(fileName, [], [], '#0000');

            expect(downloadFile).toHaveBeenCalledWith(expect.any(String), `${fileName}.pdf`);
        });
    });

    describe('getLegendsPositions', () => {
        it('single legend', async () => {
            const initialPosY = 10;
            const mockedLegend = { name: 'test', color: '#000000' };
            const [response] = getLegendsPositions(
                [mockedLegend],
                pageWidth,
                initialPosY,
                pagePadding,
                (_: string) => 100
            );

            expect(response).toEqual(
                expect.objectContaining({
                    rect: expect.objectContaining({
                        color: mockedLegend.color,
                        x: pagePadding,
                        y: initialPosY + pagePadding,
                    }),
                    text: expect.objectContaining({ name: mockedLegend.name }),
                })
            );
        });

        it('multiple legends on single line', async () => {
            const initialPosY = 10;
            const mockedLegends = [
                { name: 'test-1', color: '#000000' },
                { name: 'test-2', color: '#ffffff' },
                { name: 'test-3', color: '#000000' },
            ];
            const response = getLegendsPositions(
                mockedLegends,
                pageWidth,
                initialPosY,
                pagePadding,
                (text: string) => text.length
            );

            expect(response).toEqual(
                expect.arrayContaining([
                    expect.objectContaining({
                        rect: expect.objectContaining({
                            color: mockedLegends[0].color,
                            y: initialPosY + pagePadding,
                        }),
                    }),
                    expect.objectContaining({
                        rect: expect.objectContaining({
                            color: mockedLegends[1].color,
                            y: initialPosY + pagePadding,
                        }),
                    }),
                    expect.objectContaining({
                        rect: expect.objectContaining({
                            color: mockedLegends[2].color,
                            y: initialPosY + pagePadding,
                        }),
                    }),
                ])
            );
        });

        it('multiple legends on multiple lines', async () => {
            const initialPosY = 10;
            const mockedLegends = [
                { name: 'test-1', color: '#000000' },
                { name: 'test-2', color: '#ffffff' },
                { name: 'test-3', color: '#000000' },
            ];
            const response = getLegendsPositions(
                mockedLegends,
                pageWidth,
                initialPosY,
                pagePadding,
                (_: string) => pageWidth - 30
            );

            expect(response).toEqual(
                expect.arrayContaining([
                    expect.objectContaining({
                        rect: expect.objectContaining({
                            color: mockedLegends[0].color,
                            x: pagePadding,
                            y: initialPosY + pagePadding,
                        }),
                    }),
                    expect.objectContaining({
                        rect: expect.objectContaining({
                            color: mockedLegends[1].color,
                            x: pagePadding,
                            y: 50,
                        }),
                    }),
                    expect.objectContaining({
                        rect: expect.objectContaining({
                            color: mockedLegends[2].color,
                            x: pagePadding,
                            y: 70,
                        }),
                    }),
                ])
            );
        });
    });

    describe('getElementSize', () => {
        it('small canvas', async () => {
            const svgY = 20;
            const svg = getMockedSvg(200, 200);
            expect(getElementSize(svg, svgY, pageWidth, pageHeight, 10)).toEqual([
                svg.clientWidth,
                svg.clientHeight,
                100,
                svgY + svg.clientHeight,
            ]);
        });

        it('larger width', async () => {
            const svgY = 20;
            const svg = getMockedSvg(600, 300);
            const [canvasWidth, canvasHeight] = getElementSize(svg, svgY, pageWidth, pageHeight, pagePadding);

            expect(canvasWidth).toBe(pageWidth - pagePadding);
            expect(canvasHeight).toBeLessThan(svg.clientHeight);
        });

        it('larger height', async () => {
            const svgY = 20;
            const svg = getMockedSvg(300, 600);
            const [canvasWidth, canvasHeight] = getElementSize(svg, svgY, pageWidth, pageHeight, pagePadding);
            expect(canvasWidth).toBeLessThan(pageWidth);
            expect(canvasHeight).toBeLessThan(pageHeight);
        });

        it('large svgY', async () => {
            const svgY = 100;
            const svg = getMockedSvg(300, 300);
            const [canvasWidth, canvasHeight] = getElementSize(svg, svgY, pageWidth, pageHeight, pagePadding);
            expect(canvasWidth).toBeLessThan(pageWidth);
            expect(canvasHeight).toBeLessThan(pageHeight);
        });
    });

    describe('getContainerElements', () => {
        it('null element', () => {
            expect(getContainerElements(null, 'selector')).toEqual([]);
        });

        it('null selector match', () => {
            const element = { querySelectorAll: jest.fn(() => null) } as unknown as Element;

            expect(getContainerElements(element, 'selector')).toEqual([]);
        });

        it('selector match', () => {
            const result = 'result';
            const element = { querySelectorAll: jest.fn(() => [result]) } as unknown as Element;

            expect(getContainerElements(element, 'selector')).toEqual([result]);
        });
    });
});
