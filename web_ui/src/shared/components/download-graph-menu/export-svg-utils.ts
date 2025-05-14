// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import type { jsPDF } from 'jspdf';
import { isEmpty, isNil, negate } from 'lodash-es';

import base64Encodedfont from '../../../assets/fonts/intel-clear.font';
import { downloadFile, runWhen } from '../../utils';

const PAGE_PADDING = 40;
const PAGE_FONT_SIZE = 14;

export const DOWNLOADABLE_SVG_LABEL = 'downloadable svg';
export const DOWNLOADABLE_SVG_SELECTOR = `svg[aria-valuetext="${DOWNLOADABLE_SVG_LABEL}"]`;
export const DOWNLOADABLE_HTML_LABEL = 'downloadable html';
export const DOWNLOADABLE_HTML_SELECTOR = `[aria-valuetext="${DOWNLOADABLE_HTML_LABEL}"]`;
export const ERROR_MESSAGE = 'Something went wrong while attempting to download the PDF file, please try again.';

interface Legend {
    rect: {
        x: number;
        y: number;
        size: number;
        color: string;
    };
    text: {
        x: number;
        y: number;
        name: string;
    };
}

export interface SvgLegend {
    name: string;
    color: string;
}

const setCssInlineProperty = runWhen(negate(isEmpty))((
    elements: (SVGElement | HTMLElement)[],
    properties: string[]
) => {
    elements.forEach((element) =>
        properties
            .map((property) => window.getComputedStyle(element).getPropertyValue(property))
            .forEach((computedStyle, index) => (element.style[properties[index] as unknown as number] = computedStyle))
    );
});

export const getLegendsPositions = (
    legends: SvgLegend[],
    pageWidth: number,
    initialPosY: number,
    pagePadding: number,
    getTextWidth: (text: string) => number
): Legend[] => {
    const newLineMargin = 20;
    const getTextSize = (text: string) => (x: number) => x + getTextWidth(text) + 10;
    const getLegendPosition = (initX: number, initY: number) => {
        const textMarginLeft = 6;
        const rect = { size: 10, x: initX, y: initY };
        const text = { x: rect.x + rect.size + textMarginLeft, y: rect.y };
        return { rect, text };
    };

    let pointer = { posX: pagePadding, posY: initialPosY + newLineMargin };
    return legends.reduce((previousValue: Legend[], { color, name }: SvgLegend, currentIndex): Legend[] => {
        const getTextEnd = getTextSize(name);

        const isFirstItem = currentIndex === 0;
        const { rect, text } = getLegendPosition(pointer.posX, pointer.posY);
        const textEnd = getTextEnd(text.x);
        const isOffPageWidth = textEnd > pageWidth;

        if (!isFirstItem && isOffPageWidth) {
            const newLineY = pointer.posY + newLineMargin;
            const newLineLegend = getLegendPosition(pagePadding, newLineY);
            const finalTextEnd = getTextEnd(newLineLegend.text.x);

            pointer = { posX: finalTextEnd, posY: newLineY };
            return [
                ...previousValue,
                { rect: { color, ...newLineLegend.rect }, text: { name, ...newLineLegend.text } },
            ];
        }

        pointer = { ...pointer, posX: textEnd };
        return [...previousValue, { rect: { color, ...rect }, text: { name, ...text } }];
    }, []);
};

export const getElementSize = (
    { clientWidth, clientHeight }: { clientWidth: number; clientHeight: number },
    canvasY: number,
    pageWidth: number,
    pageHeight: number,
    pagePadding: number
): [number, number, number, number] => {
    const pageCenter = pageWidth / 2;
    const ratio = clientHeight / clientWidth;
    const newWidth = clientWidth + pagePadding > pageWidth ? pageWidth - pagePadding : clientWidth;
    const newHeight = ratio * newWidth;

    const elementHeight = newHeight > pageHeight - canvasY ? pageHeight - pagePadding - canvasY : newHeight;
    const elementWidth = elementHeight / ratio;
    const center = pageCenter - elementWidth / 2;
    const svgEnd = elementHeight + canvasY;

    return [elementWidth, elementHeight, center, svgEnd];
};

export const downloadMultiplePages = async (
    fileName: string,
    svgs: SVGElement[],
    divs: HTMLDivElement[],
    backgroundColor: string
) => {
    const { jsPDF } = await import('jspdf');

    const doc = new jsPDF({ unit: 'px' });

    doc.addFileToVFS('intelOne.ttf', base64Encodedfont);
    doc.addFont('intelOne.ttf', 'intelOne', 'normal');

    doc.setFontSize(PAGE_FONT_SIZE);
    doc.setFont('intelOne');

    await addSvgElements(doc, svgs, backgroundColor);
    await addHTMLElements(doc, divs);

    downloadFile(doc.output('datauristring'), `${fileName}.pdf`);
};

const formatLegendColor = ({ name, color }: SvgLegend) => ({
    name,
    color: isVariableColor(color) ? getVarColorToHex(color) : color,
});

const addSvgElements = async (doc: jsPDF, svgs: SVGElement[], backgroundColor: string): Promise<void> => {
    if (isEmpty(svgs)) {
        return;
    }

    const { svg2pdf } = await import('svg2pdf.js');

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const pageCenter = pageWidth / 2;

    const svgsInlineStyles = svgs.map(setInlineSvgStyles);
    const lastSvg = svgsInlineStyles[svgsInlineStyles.length - 1];

    for await (const currentSvg of svgsInlineStyles) {
        const canvasY = 50;
        const isLastElement = currentSvg === lastSvg;
        const title = String(currentSvg.getAttribute('aria-label'));
        const legend: SvgLegend[] = JSON.parse(String(currentSvg.getAttribute('aria-details'))) ?? [];
        const formattedLegend = legend.map(formatLegendColor);

        const [svgWidth, svgHeight, xToCenter, svgEnd] = getElementSize(
            currentSvg,
            canvasY,
            pageWidth,
            pageHeight,
            PAGE_PADDING
        );

        doc.text(title, pageCenter, 20, { align: 'center', baseline: 'top' });

        await svg2pdf(setSvgBackground(currentSvg, backgroundColor), doc, {
            y: canvasY,
            x: xToCenter,
            width: svgWidth,
            height: svgHeight,
        });

        getLegendsPositions(formattedLegend, pageWidth, svgEnd, PAGE_PADDING, doc.getTextWidth.bind(doc)).forEach(
            ({ rect, text }) => {
                const sixLetterHexColor = rect.color.slice(0, 7);
                const hasFillColor = sixLetterHexColor !== '';

                hasFillColor && doc.setFillColor(sixLetterHexColor);
                doc.rect(rect.x, rect.y, rect.size, rect.size, hasFillColor ? 'F' : 'S');
                doc.text(text.name, text.x, text.y, { align: 'left', baseline: 'top' });
            }
        );

        !isLastElement && doc.addPage();
    }
};

const setPageOrientation = (otherDoc: jsPDF, elementWidth: number): { pageWidth: number; pageHeight: number } => {
    const pageWidth = otherDoc.internal.pageSize.getWidth() - PAGE_PADDING;
    const totalPages = otherDoc.getNumberOfPages();

    if (elementWidth > pageWidth) {
        otherDoc.deletePage(totalPages);
        otherDoc.addPage('a4', 'landscape');
    }

    return {
        pageWidth: otherDoc.internal.pageSize.getWidth() - PAGE_PADDING,
        pageHeight: otherDoc.internal.pageSize.getHeight() - PAGE_PADDING,
    };
};

const addHTMLElements = async (doc: jsPDF, divs: HTMLDivElement[] | null) => {
    const HEIGHT_PADDING = 30;

    if (divs === null) {
        throw new Error('divs are not present');
    }

    const { default: html2canvas } = await import('html2canvas');

    for (const div of divs) {
        doc.getNumberOfPages() > 1 && doc.addPage();

        const width = div.offsetWidth;
        const height = div.offsetHeight;

        const { pageWidth, pageHeight } = setPageOrientation(doc, width);

        const scale = pageWidth / div.scrollWidth;

        // change background color to be the same color as the html page
        const rootStyle = div.getAttribute('style');
        div.setAttribute('style', rootStyle + ' background-color: var(--spectrum-global-color-gray-100);');

        const canvas = await html2canvas(div, { scale: scale > 1 ? 1 : scale });
        const imageData = canvas.toDataURL('image/png');

        const ratio = width / height;
        const imgWidth = pageWidth;
        const imgHeight = Math.min(imgWidth / ratio, pageHeight) - HEIGHT_PADDING;

        const canvasY = 50;

        const title = div.ariaLabel ?? '';
        const pageCenter = pageWidth / 2;

        doc.text(title, pageCenter, 20, { align: 'center', baseline: 'top' });
        doc.addImage(imageData, 'png', PAGE_PADDING / 2, canvasY, imgWidth, imgHeight);
    }
};

const setSvgBackground = (svg: SVGElement, backgroundColor: string): SVGElement => {
    const backgroundRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    backgroundRect.setAttribute('width', `${svg.clientWidth}`);
    backgroundRect.setAttribute('height', `${svg.clientHeight}`);
    backgroundRect.setAttribute('fill', backgroundColor);

    svg.insertBefore(backgroundRect, svg.firstElementChild);

    return svg;
};

// XMLSerializer does not keep a reference to CSS classes and thus, we need to set inline CSS
const setInlineSvgStyles = (svg: SVGElement): SVGElement => {
    setCssInlineProperty(getContainerElements(svg, 'tspan'), ['fill', 'font-family', 'font-size']);
    setCssInlineProperty(getContainerElements(svg, 'text'), ['fill', 'font-family', 'font-size']);
    setCssInlineProperty(getContainerElements(svg, '.recharts-line path'), ['fill', 'stroke']);
    setCssInlineProperty(getContainerElements(svg, '.recharts-area path'), ['fill', 'stroke']);
    setCssInlineProperty(getContainerElements(svg, '.recharts-pie path'), ['fill', 'stroke']);
    setCssInlineProperty(getContainerElements(svg, 'path.recharts-symbols'), ['fill', 'stroke']);

    return svg;
};

const isVariableColor = (variableName: string) => variableName.startsWith('var(--') && variableName.endsWith(')');

export const getVarColorToHex = (variableName: string) => {
    const themeProvider = document.getElementById('theme-provider');

    if (themeProvider === null) {
        return '';
    }

    const cleanName = variableName.replace('var(', '').replace(')', '');
    const computedStyle = getComputedStyle(themeProvider);
    return computedStyle.getPropertyValue(cleanName).trim();
};

export const getContainerElements = <T extends Element>(container: Element | null, selector: string): T[] => {
    if (isNil(container)) {
        return [];
    }

    return Array.from(container.querySelectorAll<T>(selector) ?? []);
};
