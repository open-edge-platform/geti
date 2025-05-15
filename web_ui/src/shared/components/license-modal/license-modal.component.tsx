// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Flex, Heading, Text } from '@adobe/react-spectrum';
import { isFunction } from 'lodash-es';

import { useProfileQuery } from '../../../core/users/hook/use-profile.hook';
import { useUsers } from '../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { Button } from '../button/button.component';

import classes from './license-modal.module.scss';

interface LicenseModalProps {
    onClose?: () => void;
    forceOpen?: boolean;
}
export const LicenseModal = ({ onClose, forceOpen }: LicenseModalProps) => {
    const { data: profileData } = useProfileQuery();
    const [isOpen, setIsOpen] = useState(true);

    const { organizationId } = useOrganizationIdentifier();
    const { useActiveUser, useUpdateUser } = useUsers();
    const { data: activeUser } = useActiveUser(organizationId);
    const updateUser = useUpdateUser();

    const userHasAcceptedPermissions = profileData.hasAcceptedUserTermsAndConditions === true;
    const isModalOpen = (!userHasAcceptedPermissions && isOpen) || forceOpen;

    const handleAcceptLicense = () => {
        if (!activeUser) return;

        updateUser.mutate(
            {
                user: { ...activeUser, userConsent: 'y' },
                userId: activeUser.id,
                organizationId,
            },
            {
                onSettled: () => {
                    setIsOpen(false);
                },
            }
        );
    };

    const handleDismissModal = () => {
        setIsOpen(false);
        isFunction(onClose) && onClose();
    };

    return (
        <DialogContainer onDismiss={handleDismissModal} isKeyboardDismissDisabled>
            {isModalOpen && (
                <Dialog maxHeight={'70vh'} UNSAFE_className={classes.licenseModal}>
                    <Heading marginBottom={'size-300'}>LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE AGREEMENT</Heading>
                    <Content>
                        <Flex direction={'column'} gap={'size-100'}>
                            <Text>
                                This LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE AGREEMENT (“Agreement”) is a contract
                                between you and Intel Corporation and its affiliates (“Intel”) and governs use of
                                Material. If you use Material on behalf of or in connection with your employment, you
                                represent and warrant that you have the authority to bind your employer (and its
                                affiliates) to this Agreement. By downloading, installing, or using Material, you accept
                                these terms on your own behalf or on behalf of your employer, as applicable. If you do
                                not accept these terms, do not use any Material and destroy all copies of Material.
                            </Text>
                            <Divider marginTop={'size-100'} size={'S'} />
                            <Text>1 DEFINITIONS.</Text>
                            <Text>
                                1.1 “Including”, and its variants, whether or not capitalized, means including but not
                                limited to.
                            </Text>
                            <Text>
                                1.2 “Intel Component” means a hardware component designed, developed, sold, or
                                distributed by Intel.
                            </Text>
                            <Text>
                                1.3 “Material” means software, hardware description language code, or other computer
                                files, information or collateral Intel delivers to you under this Agreement.
                            </Text>
                            <Text>
                                1.4 “You” or “Your”, whether or not capitalized, means you or you and your employer and
                                its affiliates.
                            </Text>
                            <Text>
                                1.5 “Your Product” means product or a solution developed or to be developed by or for
                                you that includes an Intel Component implementing or executing Material.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>2 LICENSES.</Text>
                            <Text>
                                2.1 License. Subject to the terms of this Agreement, Intel grants to you, for the Term,
                                a personal, limited, non-transferable, nonexclusive, worldwide, revocable, fully paid-up
                                license under Intel&apos;s intellectual property rights in the Material, without the
                                right to sublicense, to: a) develop Your Product; b) modify Material delivered by Intel
                                as source code (or its equivalent); and c) distribute Material, as delivered by Intel or
                                as modified by you (where expressly permitted), as object code (or its equivalent), in
                                Your Product, provided your distribution is subject to terms and conditions consistent
                                with your rights and obligations under this Agreement.
                            </Text>
                            <Text>
                                2.2 Subcontractor. You may disclose Material to your subcontractor for its work on Your
                                Product under an agreement preventing the subcontractor from disclosing Material to
                                others. You will be liable for the acts or omissions of your subcontractor.
                            </Text>
                            <Text>
                                2.3 Restrictions. Except as authorized above, you will not: (a) use or modify Material
                                in any other way, (b) reverse engineer, decompile, or disassemble Material provided as
                                object code (except as required by applicable law or under an applicable open source
                                license), (c) distribute Your Product or use Your Product in a production environment,
                                or (d) use Material to violate or aid in the violation of any international human right.
                            </Text>
                            <Text>
                                2.4 No Implied License. Except for the express license in Section 2.1 Intel does not
                                grant you (i) any express or implied license under any legal theory, or (ii) or any
                                license to make, have made, use, sell, offer for sale, import, or otherwise dispose of
                                any Intel technology or third-party products, or perform any patented process, even if
                                referenced in the Material. Any other licenses from Intel require additional
                                consideration. Nothing in this Agreement requires Intel to grant any additional license.
                            </Text>
                            <Text>
                                2.5 Feedback. If you give Intel comments or suggestions related to Intel Components or
                                information provided in connection with this Agreement, including Material, Intel can
                                use them in any way and disclose them to anyone, without payment or other obligations to
                                you.
                            </Text>
                            <Text>
                                2.6 Open Source Licenses. The Material may include software subject to an open source
                                license, including Open Source Initiative approved licenses (http://www.opensource.org).
                                Nothing in this Agreement limits or grants any rights under, or that supersede, the
                                terms of any applicable open source license.
                            </Text>
                            <Text>
                                2.7 Third-Party Software. Your use of certain third-party software with or within the
                                Material is subject to your compliance with licensing you obtain directly from that
                                third-party. A listing of any such third-party software may accompany the Material.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>3. [intentionally left blank].</Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>
                                4 OWNERSHIP. Ownership of the Material and related intellectual property rights is
                                unchanged. You must maintain all copyright or other proprietary notices in the Material.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>
                                5 NO WARRANTY. The Material is provided “as is,” without any express or implied warranty
                                of any kind including warranties of merchantability, non-infringement, title, or fitness
                                for a particular purpose. The Material may be pre-release and may not be fully
                                functional. Intel is not required to maintain, update, or support any Material.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>
                                6 LIMITATION ON LIABILITY. Your use of Material is at your own risk. Intel will not be
                                liable to you under any legal theory for any losses or damages in connection with the
                                Material or your use of Material, including consequential damages, even if the
                                possibility of damages was foreseeable or known. If any liability is found, Intel&apos;s
                                total, cumulative liability to you for all claims arising from or related to this
                                Agreement will not exceed $100.00 U.S. These liability limitations are a fundamental
                                basis of our bargain and Intel would not have entered into this Agreement without them.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>
                                7 INDEMNITY. You will indemnify, defend, and hold Intel harmless from any allegation
                                against Intel arising in connection with your use of Material and you will pay all of
                                Intel&apos;s losses, liabilities, and costs (including reasonable attorneys&apos; fees)
                                arising from the allegation.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>8 PRIVACY; DATA COLLECTION.</Text>
                            <Text>
                                8.1 Privacy. Intel&apos;s Privacy Notice governs how Intel may process personal
                                information related to your use of Material (see https://www.intel.com/privacy). Intel
                                may collect identifying information during registration and information on your use of
                                Material (see “Information You Provide to Intel Voluntarily” and “Device and Product
                                Operation” sections).
                            </Text>
                            <Text>
                                8.2 Data Collection. Some Material may generate, collect, and transmit to Intel
                                information to help improve Intel&apos;s products and services, to verify your license
                                rights to Material, or for other stated purposes. Information collected may include
                                Intel Component or Material name and version, time of event collection, license or
                                support type, installation status, performance, and use. Intel&apos;s use of information
                                may include combination of the information collected from you with other information.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>9 GENERAL.</Text>
                            <Text>
                                9.1 Assignment. You may not assign your rights or obligations under this Agreement
                                without Intel&apos;s prior written consent. No third party will have any rights under
                                this Agreement.
                            </Text>
                            <Text>
                                9.2 Dispute Resolution. If we have a dispute regarding this Agreement (other than for
                                misappropriation of trade secrets) neither party can file a lawsuit or other regulatory
                                proceeding before the complaining party provides the other party a detailed notice of
                                the dispute and our senior managers attempt to resolve the dispute. If our senior
                                managers cannot resolve the dispute in 30 days, either party may demand mediation in
                                which we will then try to resolve the dispute with an impartial mediator. If our dispute
                                is not resolved within 60 days after the mediation demand, either party may begin
                                litigation.
                            </Text>
                            <Text>
                                9.3 Governing Law; Jurisdiction. This Agreement is governed by USA and Delaware law
                                without regard to conflict of laws principles. The United Nations Convention on
                                Contracts for the International Sale of Goods does not apply. Except for claims for
                                misappropriation of trade secrets, all disputes and actions arising out of or related to
                                this Agreement are subject to the exclusive jurisdiction of the state and federal courts
                                in Wilmington, Delaware and you consent to personal jurisdiction in those courts.
                            </Text>
                            <Text>
                                9.4 Compliance with Laws. The Material is subject to, and You must comply with,
                                applicable government laws and regulations, including without limitation U.S. and
                                worldwide trade regulations prohibiting the export, import, or transfer Material to any
                                prohibited or sanctioned country, person, or entity. You must not use Material for the
                                development, design, manufacture, or production of nuclear, missile, chemical, or
                                biological weapons.
                            </Text>
                            <Text>
                                9.5 Severability. If a court holds a provision of this Agreement unenforceable, the
                                court will modify that provision to the minimum extent necessary to make it enforceable
                                or, if necessary, to sever that provision. The rest of the Agreement remains
                                enforceable.
                            </Text>
                            <Text>
                                9.6 Waiver. No waiver of any provision of this Agreement will be valid unless in a
                                writing specifying the waived provision signed by an authorized representative of the
                                waiving party. A signed waiver will not constitute waiver of any other provision.
                                Failure or delay in enforcing any provision will not operate as a waiver.
                            </Text>
                            <Text>
                                9.7 Entire Agreement. This Agreement constitutes the entire agreement, and supersedes
                                all prior and contemporaneous agreements, between Intel and you concerning its subject
                                matter.
                            </Text>
                            <Divider marginY={'size-200'} size={'S'} />
                            <Text>10 TERM; TERMINATION; SURVIVAL.</Text>
                            <Text>
                                10.1 Term. This Agreement begins upon your acceptance of its terms and continues until
                                terminated under Section 10.2.
                            </Text>
                            <Text>
                                10.2 Termination. Either party may terminate this Agreement, with 30 days written
                                notice, at any time for any reason. This Agreement will automatically terminate upon (a)
                                your breach of the Agreement, (b) a claim that you do not have authority to bind your
                                employer to these terms, (c) your assertion that any Intel Component, Material, or
                                product based on any Intel Component or Material infringes your patents, or (d) as
                                specified in a Term Addendum included with the Material.
                            </Text>
                            <Text>
                                10.3 Effect of Termination. Upon termination of the Agreement, the licenses to you will
                                immediately terminate and you must cease using any Material and destroy all copies in
                                your possession and direct your subcontractors to do the same. Termination of this
                                Agreement will not terminate any CNDA that might be in place between the parties, if
                                any.
                            </Text>
                            <Text>
                                10.4 Survival. All sections except Section 2.1 survive termination of this Agreement.
                            </Text>
                        </Flex>
                    </Content>
                    <ButtonGroup>
                        <Button onPress={userHasAcceptedPermissions ? handleDismissModal : handleAcceptLicense}>
                            {userHasAcceptedPermissions ? 'Close' : 'Accept'}
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
