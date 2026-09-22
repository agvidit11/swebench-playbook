/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.apache.xml.security.test.dom.signature;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;

import org.apache.xml.security.Init;
import org.apache.xml.security.algorithms.MessageDigestAlgorithm;
import org.apache.xml.security.exceptions.XMLSecurityException;
import org.apache.xml.security.signature.Manifest;
import org.apache.xml.security.signature.MissingResourceFailureException;
import org.apache.xml.security.signature.ObjectContainer;
import org.apache.xml.security.signature.Reference;
import org.apache.xml.security.signature.VerifiedReference;
import org.apache.xml.security.signature.XMLSignature;
import org.apache.xml.security.signature.XMLSignatureByteInput;
import org.apache.xml.security.signature.XMLSignatureInput;
import org.apache.xml.security.test.XmlSecTestEnvironment;
import org.apache.xml.security.test.dom.TestUtils;
import org.apache.xml.security.utils.Constants;
import org.apache.xml.security.utils.ElementProxy;
import org.apache.xml.security.utils.resolver.ResourceResolverContext;
import org.apache.xml.security.utils.resolver.ResourceResolverException;
import org.apache.xml.security.utils.resolver.ResourceResolverSpi;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

/**
 * Executable characterisation probes for Manifest reference limits and result reporting.
 */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class ProbeManifestPolicyTest {

    private static final String DIGEST_ALGORITHM = MessageDigestAlgorithm.ALGO_ID_DIGEST_SHA256;
    private static final String MISSING_URI = "urn:probe:resource-that-verifier-cannot-resolve";

    ProbeManifestPolicyTest() throws Exception {
        Init.init();
        ElementProxy.setDefaultPrefix(Constants.SignatureSpecNS, "ds");
    }

    @Test
    @Order(1)
    void question1ReferenceBudgets() throws Exception {
        SignatureFixture flat31 = createFlatFixture(31);
        XMLSecurityException tooMany = assertThrows(
            XMLSecurityException.class,
            () -> verifier(flat31)
        );
        System.out.println("PROBE Q1a flat=31 exception=" + tooMany.getClass().getName()
            + " msgID=" + tooMany.getMsgID());
        assertEquals("signature.tooManyReferences", tooMany.getMsgID());

        SignatureFixture flat30 = createFlatFixture(30);
        XMLSignature flat30Verifier = verifier(flat30);
        boolean flat30Valid = flat30Verifier.checkSignatureValue(flat30.publicKey);
        System.out.println("PROBE Q1b flat=30 completed=true valid=" + flat30Valid
            + " results=" + flat30Verifier.getSignedInfo().getVerificationResults().size());
        assertTrue(flat30Valid);
        assertEquals(30, flat30Verifier.getSignedInfo().getVerificationResults().size());

        SignatureFixture nested = createNestedBudgetFixture(25, 25);
        XMLSignature nestedVerifier = verifier(nested);
        nestedVerifier.setFollowNestedManifests(true);
        boolean nestedValid = nestedVerifier.checkSignatureValue(nested.publicKey);
        List<VerifiedReference> nestedResults = nestedVerifier.getSignedInfo().getVerificationResults();
        VerifiedReference manifestResult = nestedResults.get(nestedResults.size() - 1);
        System.out.println("PROBE Q1c top=25 nested=25 total=50 completed=true valid=" + nestedValid
            + " topResults=" + nestedResults.size()
            + " nestedResults=" + manifestResult.getManifestReferences().size());
        assertTrue(nestedValid);
        assertEquals(25, nestedResults.size());
        assertEquals(25, manifestResult.getManifestReferences().size());
    }

    @Test
    @Order(2)
    void question2NestedManifestResultReporting() throws Exception {
        ThreeReferenceFixture secondMismatch = createThreeReferenceFixture();
        secondMismatch.ordinaryElement.setTextContent("ordinary content changed after signing");

        XMLSignature secondMismatchVerifier = verifier(secondMismatch.signatureFixture);
        secondMismatchVerifier.setFollowNestedManifests(true);
        boolean secondMismatchValid = secondMismatchVerifier.checkSignatureValue(
            secondMismatch.signatureFixture.publicKey
        );
        List<VerifiedReference> secondMismatchResults =
            secondMismatchVerifier.getSignedInfo().getVerificationResults();
        System.out.println("PROBE Q2 case=reference-2-mismatch overallValid=" + secondMismatchValid);
        printResults("Q2 reference-2-mismatch", secondMismatchResults);
        assertFalse(secondMismatchValid);
        assertEquals(3, secondMismatchResults.size());
        assertEquals(1, secondMismatchResults.get(0).getManifestReferences().size());
        assertEquals(0, secondMismatchResults.get(2).getManifestReferences().size());

        ThreeReferenceFixture firstMismatch = createThreeReferenceFixture();
        firstMismatch.firstManifest.getElement().setAttributeNS(null, "changedAfterSigning", "true");

        XMLSignature firstMismatchVerifier = verifier(firstMismatch.signatureFixture);
        firstMismatchVerifier.setFollowNestedManifests(true);
        boolean firstMismatchValid = firstMismatchVerifier.checkSignatureValue(
            firstMismatch.signatureFixture.publicKey
        );
        List<VerifiedReference> firstMismatchResults =
            firstMismatchVerifier.getSignedInfo().getVerificationResults();
        System.out.println("PROBE Q2 case=reference-1-mismatch overallValid=" + firstMismatchValid);
        printResults("Q2 reference-1-mismatch", firstMismatchResults);
        System.out.println("PROBE Q2 reference-3-populated-when-reference-2-mismatches="
            + !secondMismatchResults.get(2).getManifestReferences().isEmpty());
        System.out.println("PROBE Q2 reference-3-populated-when-reference-1-mismatches="
            + !firstMismatchResults.get(2).getManifestReferences().isEmpty());
        assertFalse(firstMismatchValid);
        assertEquals(3, firstMismatchResults.size());
        assertEquals(0, firstMismatchResults.get(0).getManifestReferences().size());
        assertEquals(0, firstMismatchResults.get(2).getManifestReferences().size());
    }

    @Test
    @Order(3)
    void question3MissingResourceStopsResultCollection() throws Exception {
        FourReferenceFixture missing = createFourReferenceFixture(true);
        missing.elements.get(3).setTextContent("reference 4 changed after signing");
        XMLSignature missingVerifier = verifier(missing.signatureFixture);

        try {
            missingVerifier.checkSignatureValue(missing.signatureFixture.publicKey);
            fail("Expected an unresolved URI to throw");
        } catch (MissingResourceFailureException ex) {
            List<VerifiedReference> partialResults =
                missingVerifier.getSignedInfo().getVerificationResults();
            Reference failedReference = ex.getReference();
            System.out.println("PROBE Q3 missing exception=" + ex.getClass().getName()
                + " msgID=" + ex.getMsgID());
            System.out.println("PROBE Q3 missing results=" + partialResults.size());
            System.out.println("PROBE Q3 missing getReference.present=" + (failedReference != null)
                + " uri=" + (failedReference == null ? null : failedReference.getURI()));
            assertEquals(1, partialResults.size());
            assertNotNull(failedReference);
            assertEquals(MISSING_URI, failedReference.getURI());
        }

        FourReferenceFixture mismatches = createFourReferenceFixture(false);
        mismatches.elements.get(1).setTextContent("reference 2 changed after signing");
        mismatches.elements.get(3).setTextContent("reference 4 changed after signing");
        XMLSignature mismatchVerifier = verifier(mismatches.signatureFixture);
        boolean mismatchValid = mismatchVerifier.checkSignatureValue(mismatches.signatureFixture.publicKey);
        List<VerifiedReference> mismatchResults = mismatchVerifier.getSignedInfo().getVerificationResults();
        System.out.println("PROBE Q3 mismatch-only overallValid=" + mismatchValid
            + " results=" + mismatchResults.size());
        printResults("Q3 mismatch-only", mismatchResults);
        assertFalse(mismatchValid);
        assertEquals(4, mismatchResults.size());
    }

    @Test
    @Order(4)
    void question1dSystemPropertyTiming() throws Exception {
        String propertyName = "org.apache.xml.security.maxReferences";
        String oldValue = System.getProperty(propertyName);
        System.setProperty(propertyName, "5");
        try {
            SignatureFixture flat6 = createFlatFixture(6);
            try {
                XMLSignature flat6Verifier = verifier(flat6);
                boolean valid = flat6Verifier.checkSignatureValue(flat6.publicKey);
                System.out.println("PROBE Q1d property=5 flat=6 completed=true valid=" + valid
                    + " effect=false");
                assertTrue(valid);
            } catch (XMLSecurityException ex) {
                System.out.println("PROBE Q1d property=5 flat=6 exception=" + ex.getClass().getName()
                    + " msgID=" + ex.getMsgID() + " effect=true");
                assertEquals("signature.tooManyReferences", ex.getMsgID());
            }
        } finally {
            if (oldValue == null) {
                System.clearProperty(propertyName);
            } else {
                System.setProperty(propertyName, oldValue);
            }
        }
    }

    private SignatureFixture createFlatFixture(int referenceCount) throws Exception {
        Document doc = newProbeDocument();
        Element root = doc.getDocumentElement();
        List<Element> elements = new ArrayList<>();
        for (int i = 0; i < referenceCount; i++) {
            elements.add(addDataElement(root, "flat-" + i, "flat content " + i));
        }

        XMLSignature signature = newSignature(doc);
        for (Element element : elements) {
            signature.addDocument("#" + element.getAttributeNS(null, "Id"), null, DIGEST_ALGORITHM);
        }
        return sign(signature, doc, elements);
    }

    private SignatureFixture createNestedBudgetFixture(int topCount, int nestedCount) throws Exception {
        Document doc = newProbeDocument();
        Element root = doc.getDocumentElement();
        List<Element> topElements = new ArrayList<>();
        List<Element> nestedElements = new ArrayList<>();
        for (int i = 0; i < topCount - 1; i++) {
            topElements.add(addDataElement(root, "top-" + i, "top content " + i));
        }
        for (int i = 0; i < nestedCount; i++) {
            nestedElements.add(addDataElement(root, "nested-" + i, "nested content " + i));
        }

        XMLSignature signature = newSignature(doc);
        Manifest manifest = new Manifest(doc);
        manifest.setId("budget-manifest");
        for (Element element : nestedElements) {
            manifest.addDocument(
                "", "#" + element.getAttributeNS(null, "Id"), null, DIGEST_ALGORITHM, null, null
            );
        }
        appendManifest(signature, manifest);
        for (Element element : topElements) {
            signature.addDocument("#" + element.getAttributeNS(null, "Id"), null, DIGEST_ALGORITHM);
        }
        signature.addDocument(
            "#budget-manifest", null, DIGEST_ALGORITHM, null, Reference.MANIFEST_URI
        );
        manifest.generateDigestValues();
        return sign(signature, doc, topElements);
    }

    private ThreeReferenceFixture createThreeReferenceFixture() throws Exception {
        Document doc = newProbeDocument();
        Element root = doc.getDocumentElement();
        Element nested1Data = addDataElement(root, "nested-one-data", "nested one content");
        Element ordinary = addDataElement(root, "ordinary-two", "ordinary content");
        Element nested3Data = addDataElement(root, "nested-three-data", "nested three content");
        XMLSignature signature = newSignature(doc);

        Manifest firstManifest = createOneReferenceManifest(doc, "manifest-one", nested1Data);
        Manifest thirdManifest = createOneReferenceManifest(doc, "manifest-three", nested3Data);
        appendManifest(signature, firstManifest);
        appendManifest(signature, thirdManifest);

        signature.addDocument("#manifest-one", null, DIGEST_ALGORITHM, null, Reference.MANIFEST_URI);
        signature.addDocument("#ordinary-two", null, DIGEST_ALGORITHM);
        signature.addDocument("#manifest-three", null, DIGEST_ALGORITHM, null, Reference.MANIFEST_URI);
        firstManifest.generateDigestValues();
        thirdManifest.generateDigestValues();

        List<Element> elements = new ArrayList<>();
        elements.add(nested1Data);
        elements.add(ordinary);
        elements.add(nested3Data);
        SignatureFixture fixture = sign(signature, doc, elements);
        return new ThreeReferenceFixture(fixture, ordinary, firstManifest);
    }

    private FourReferenceFixture createFourReferenceFixture(boolean unresolvedSecond) throws Exception {
        Document doc = newProbeDocument();
        Element root = doc.getDocumentElement();
        List<Element> elements = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            elements.add(addDataElement(root, "four-" + i, "four content " + i));
        }
        XMLSignature signature = newSignature(doc);
        signature.addDocument("#four-0", null, DIGEST_ALGORITHM);
        if (unresolvedSecond) {
            signature.addResourceResolver(new SigningOnlyResourceResolver());
            signature.addDocument(MISSING_URI, null, DIGEST_ALGORITHM);
        } else {
            signature.addDocument("#four-1", null, DIGEST_ALGORITHM);
        }
        signature.addDocument("#four-2", null, DIGEST_ALGORITHM);
        signature.addDocument("#four-3", null, DIGEST_ALGORITHM);
        return new FourReferenceFixture(sign(signature, doc, elements), elements);
    }

    private Manifest createOneReferenceManifest(Document doc, String id, Element target) throws Exception {
        Manifest manifest = new Manifest(doc);
        manifest.setId(id);
        manifest.addDocument(
            "", "#" + target.getAttributeNS(null, "Id"), null, DIGEST_ALGORITHM, null, null
        );
        return manifest;
    }

    private void appendManifest(XMLSignature signature, Manifest manifest) throws Exception {
        ObjectContainer object = new ObjectContainer(signature.getDocument());
        object.appendChild(manifest.getElement());
        signature.appendObject(object);
    }

    private Document newProbeDocument() throws Exception {
        Document doc = TestUtils.newDocument();
        Element root = doc.createElementNS("urn:probe", "probe:root");
        doc.appendChild(root);
        return doc;
    }

    private Element addDataElement(Element root, String id, String text) {
        Document doc = root.getOwnerDocument();
        Element element = doc.createElementNS("urn:probe", "probe:data");
        element.setAttributeNS(null, "Id", id);
        element.setIdAttributeNS(null, "Id", true);
        element.setTextContent(text);
        root.appendChild(element);
        return element;
    }

    private XMLSignature newSignature(Document doc) throws Exception {
        XMLSignature signature = new XMLSignature(doc, "", XMLSignature.ALGO_ID_SIGNATURE_DSA);
        doc.getDocumentElement().appendChild(signature.getElement());
        return signature;
    }

    private SignatureFixture sign(XMLSignature signature, Document doc, List<Element> elements) throws Exception {
        KeyStore keyStore = XmlSecTestEnvironment.getTestKeyStore();
        PublicKey publicKey = getPublicKey(keyStore);
        signature.addKeyInfo(publicKey);
        signature.sign(getPrivateKey(keyStore));
        return new SignatureFixture(doc, signature, publicKey, elements);
    }

    private XMLSignature verifier(SignatureFixture fixture) throws XMLSecurityException {
        return new XMLSignature(fixture.signature.getElement(), "", true);
    }

    private void printResults(String label, List<VerifiedReference> results) {
        for (int i = 0; i < results.size(); i++) {
            VerifiedReference result = results.get(i);
            System.out.println("PROBE " + label + " entry=" + (i + 1)
                + " uri=" + result.getUri()
                + " valid=" + result.isValid()
                + " manifestReferences=" + result.getManifestReferences().size());
        }
    }

    private PublicKey getPublicKey(KeyStore keyStore) throws Exception {
        Enumeration<String> aliases = keyStore.aliases();
        while (aliases.hasMoreElements()) {
            String alias = aliases.nextElement();
            if (keyStore.isKeyEntry(alias)) {
                return keyStore.getCertificate(alias).getPublicKey();
            }
        }
        return null;
    }

    private PrivateKey getPrivateKey(KeyStore keyStore) throws Exception {
        Enumeration<String> aliases = keyStore.aliases();
        while (aliases.hasMoreElements()) {
            String alias = aliases.nextElement();
            if (keyStore.isKeyEntry(alias)) {
                return (PrivateKey) keyStore.getKey(
                    alias, XmlSecTestEnvironment.TEST_KS_PASSWORD.toCharArray()
                );
            }
        }
        return null;
    }

    private static class SignatureFixture {
        private final Document document;
        private final XMLSignature signature;
        private final PublicKey publicKey;
        private final List<Element> elements;

        SignatureFixture(
            Document document, XMLSignature signature, PublicKey publicKey, List<Element> elements
        ) {
            this.document = document;
            this.signature = signature;
            this.publicKey = publicKey;
            this.elements = elements;
        }
    }

    private static class ThreeReferenceFixture {
        private final SignatureFixture signatureFixture;
        private final Element ordinaryElement;
        private final Manifest firstManifest;

        ThreeReferenceFixture(
            SignatureFixture signatureFixture, Element ordinaryElement, Manifest firstManifest
        ) {
            this.signatureFixture = signatureFixture;
            this.ordinaryElement = ordinaryElement;
            this.firstManifest = firstManifest;
        }
    }

    private static class FourReferenceFixture {
        private final SignatureFixture signatureFixture;
        private final List<Element> elements;

        FourReferenceFixture(SignatureFixture signatureFixture, List<Element> elements) {
            this.signatureFixture = signatureFixture;
            this.elements = elements;
        }
    }

    private static class SigningOnlyResourceResolver extends ResourceResolverSpi {
        @Override
        public XMLSignatureInput engineResolveURI(ResourceResolverContext context)
            throws ResourceResolverException {
            XMLSignatureInput result = new XMLSignatureByteInput(
                "signing-only resource".getBytes(StandardCharsets.UTF_8)
            );
            result.setSourceURI(context.uriToResolve);
            return result;
        }

        @Override
        public boolean engineCanResolveURI(ResourceResolverContext context) {
            return MISSING_URI.equals(context.uriToResolve);
        }
    }
}
