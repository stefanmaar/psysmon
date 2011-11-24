{{ fullname }}
{{ underline }}

.. currentmodule:: {{ module }}
.. automethod:: {{ objname }}

   {% block attributes %}
   .. rubric:: Documenting a method

   {% print members %}

   {% if attributes %}
   .. rubric:: Attributesss

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}
