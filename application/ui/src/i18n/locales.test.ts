// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import ts from 'typescript';

import { DEFAULT_LANGUAGE, resources, SUPPORTED_LANGUAGES } from './locales';
import en from './locales/en.json';

const sourceRoot = join(process.cwd(), 'src');
const sourceFiles = readdirSync(sourceRoot, { recursive: true, encoding: 'utf8' })
    .filter(
        (file) => /\.tsx?$/.test(file) && !/(\.test\.|\.spec\.|\.d\.ts$|test-utils|setup-tests|__mocks__)/.test(file)
    )
    .map((file) =>
        ts.createSourceFile(file, readFileSync(join(sourceRoot, file), 'utf8'), ts.ScriptTarget.Latest, true)
    );

const visitNodes = (node: ts.Node, visitor: (node: ts.Node) => void): void => {
    visitor(node);
    ts.forEachChild(node, (child) => visitNodes(child, visitor));
};

const flattenTranslations = (object: object, prefix = ''): [string, string][] =>
    Object.entries(object).flatMap(([key, value]) =>
        typeof value === 'string' ? [[`${prefix}${key}`, value]] : flattenTranslations(value, `${prefix}${key}.`)
    );

const translations = flattenTranslations(en);

const location = (source: ts.SourceFile, node: ts.Node): string =>
    `${source.fileName}:${source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1}`;

describe('locale registry', () => {
    it('registers a translation resource for every locale', () => {
        expect(Object.keys(resources)).toEqual(SUPPORTED_LANGUAGES);
        SUPPORTED_LANGUAGES.forEach((tag) => {
            expect(resources[tag]).toHaveProperty('translation');
        });
    });

    it('ships English as the default and only supported language', () => {
        expect(DEFAULT_LANGUAGE).toBe('en');
        expect(SUPPORTED_LANGUAGES).toEqual(['en']);
        expect(resources.en.translation).toHaveProperty('common.labels.dataset', 'Dataset');
    });
});

describe('translation coverage', () => {
    it('has no unused English keys, including plural variants and computed keys', () => {
        const references = new Set<string>();
        const dynamicPrefixes = new Set<string>();

        sourceFiles.forEach((source) => {
            visitNodes(source, (node) => {
                if (ts.isStringLiteralLike(node)) references.add(node.text);
                if (ts.isTemplateExpression(node) && node.head.text.includes('.')) {
                    dynamicPrefixes.add(node.head.text);
                }
            });
        });

        expect(
            translations
                .map(([key]) => key)
                .filter(
                    (key) =>
                        !references.has(key) &&
                        !references.has(key.replace(/_(zero|one|two|few|many|other)$/, '')) &&
                        ![...dynamicPrefixes].some((prefix) => key.startsWith(prefix))
                )
        ).toEqual([]);
    });

    it('defines shared actions and labels only in common', () => {
        const commonValues = new Set(flattenTranslations(en.common).map(([, value]) => value));

        expect(translations.filter(([key, value]) => !key.startsWith('common.') && commonValues.has(value))).toEqual(
            []
        );
    });

    it('does not silently overwrite duplicate JSON properties', () => {
        const source = ts.parseJsonText('en.json', readFileSync(join(sourceRoot, 'i18n/locales/en.json'), 'utf8'));
        const duplicates: string[] = [];

        visitNodes(source, (node) => {
            if (!ts.isObjectLiteralExpression(node)) return;

            const names = new Set<string>();
            node.properties.forEach((property) => {
                const name = property.name?.getText(source);
                if (name === undefined) return;
                if (names.has(name)) duplicates.push(`${location(source, property)} ${name}`);
                names.add(name);
            });
        });

        expect(duplicates).toEqual([]);
    });

    it('keeps explicit ARIA labels out of translation calls', () => {
        const translatedLabels: string[] = [];

        sourceFiles.forEach((source) => {
            visitNodes(source, (node) => {
                if (!ts.isJsxAttribute(node) || !/aria.*label|cueLabel/i.test(node.name.getText(source))) return;

                visitNodes(node, (child) => {
                    if (ts.isCallExpression(child) && /^(t|i18n\.t)$/.test(child.expression.getText(source))) {
                        translatedLabels.push(location(source, node));
                    }
                });
            });
        });

        expect(translatedLabels).toEqual([]);
    });

    it('translates visible JSX text and text props', () => {
        const technicalText = new Set(['Geti™', ').zip', 'v', 'x', 'f', '&nbsp;']);
        const textProps =
            /^(label|title|placeholder|description|tooltip|errorMessage|alt|primaryActionLabel|secondaryActionLabel|cancelLabel)$/;
        const untranslated: string[] = [];

        sourceFiles.forEach((source) => {
            visitNodes(source, (node) => {
                let text: string | undefined;

                if (ts.isJsxText(node)) text = node.text.trim();
                if (ts.isJsxExpression(node) && node.expression && ts.isStringLiteralLike(node.expression)) {
                    if (ts.isJsxElement(node.parent) || ts.isJsxFragment(node.parent)) text = node.expression.text;
                }
                if (ts.isJsxAttribute(node) && textProps.test(node.name.getText(source))) {
                    const isHidden = node.parent.properties.some(
                        (attribute) => ts.isJsxAttribute(attribute) && attribute.name.getText(source) === 'isHidden'
                    );
                    if (isHidden) return;

                    if (node.initializer && ts.isStringLiteral(node.initializer)) text = node.initializer.text;
                    if (node.initializer && ts.isJsxExpression(node.initializer)) {
                        const expression = node.initializer.expression;
                        if (expression && ts.isStringLiteralLike(expression)) text = expression.text;
                    }
                }

                if (text && /[a-z]/i.test(text) && !technicalText.has(text)) {
                    untranslated.push(`${location(source, node)} ${text}`);
                }
            });
        });

        expect(untranslated).toEqual([]);
    });
});
