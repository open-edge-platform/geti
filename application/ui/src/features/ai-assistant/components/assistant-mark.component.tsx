// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SiClaude, SiOpenai } from 'react-icons/si';

import type { AiVendor } from '../types';

export const ChatGptMark = SiOpenai;
export const ClaudeMark = SiClaude;

export const markForVendor = (vendor: AiVendor) => (vendor === 'openai' ? ChatGptMark : ClaudeMark);
