export interface ClaimForm {
  description: string;
  principal_amount: string;
  default_date: string;
  invoice_number: string;
  invoice_date: string;
  rate_basis: string;
}

export const EMPTY_CLAIM: ClaimForm = {
  description: "",
  principal_amount: "",
  default_date: "",
  invoice_number: "",
  invoice_date: "",
  rate_basis: "yearly",
};

export interface InlineContact {
  contact_type: "company" | "person";
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  kvk_number: string;
  btw_number: string;
  visit_address: string;
  visit_postcode: string;
  visit_city: string;
  postal_address: string;
  postal_postcode: string;
  postal_city: string;
  // DF138-11: ingebedde contactpersoon. Wanneer contact_type=company en
  // linked_person_name is gevuld, maakt de wizard direct ook een Person
  // contact aan en koppelt hem aan dit bedrijf via ContactLink — zodat de
  // gebruiker niet eerst de relatie hoeft op te slaan en daarna handmatig
  // een contactpersoon hoeft toe te voegen.
  linked_person_name: string;
  linked_person_email: string;
}

export const EMPTY_INLINE_CONTACT: InlineContact = {
  contact_type: "company",
  name: "",
  contact_person: "",
  email: "",
  phone: "",
  kvk_number: "",
  btw_number: "",
  visit_address: "",
  visit_postcode: "",
  visit_city: "",
  postal_address: "",
  postal_postcode: "",
  postal_city: "",
  linked_person_name: "",
  linked_person_email: "",
};
